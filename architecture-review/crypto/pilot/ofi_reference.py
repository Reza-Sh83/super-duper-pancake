"""Offline feature oracle for OFI-L2-01. No feed, orders or execution."""
from dataclasses import dataclass
from decimal import Decimal, localcontext
import unittest


D = Decimal
NANOSECONDS = 1_000_000_000


@dataclass(frozen=True)
class Quote:
    # The caller changes segment on any readiness, epoch or metadata break.
    segment: str
    receive_index: int
    monotonic_ns: int
    bid: Decimal
    bid_size: Decimal
    ask: Decimal
    ask_size: Decimal


def contribution(previous, current):
    bid = (current.bid_size * (current.bid >= previous.bid)
           - previous.bid_size * (current.bid <= previous.bid))
    ask = (-current.ask_size * (current.ask <= previous.ask)
           + previous.ask_size * (current.ask >= previous.ask))
    return bid + ask


def scores(window):
    """Use only the prefix through the trigger. Caller supplies its last 21 quotes."""
    if len(window) != 21:
        return None
    latest = window[-1]
    for quote in window:
        values = (quote.bid, quote.bid_size, quote.ask, quote.ask_size)
        if (quote.segment != latest.segment
                or any(not value.is_finite() or value <= 0 for value in values)
                or quote.bid >= quote.ask):
            return None
    for previous, current in zip(window, window[1:]):
        if (current.receive_index <= previous.receive_index
                or current.monotonic_ns < previous.monotonic_ns):
            return None
    if latest.monotonic_ns - window[0].monotonic_ns > 5 * NANOSECONDS:
        return None
    with localcontext() as ctx:
        ctx.prec = 34
        numerator = sum(contribution(a, b) for a, b in zip(window, window[1:]))
        denominator = sum((q.bid_size + q.ask_size) / 2 for q in window[1:])
        static = (latest.bid_size - latest.ask_size) / (latest.bid_size + latest.ask_size)
        return numerator / denominator, static


class Tests(unittest.TestCase):
    def quote(self, index, *, ns=0, segment="one", bid="100", ask="101", q="2", r="2"):
        return Quote(segment, index, ns, D(bid), D(q), D(ask), D(r))

    def test_quote_movements(self):
        prior = self.quote(0)
        self.assertEqual(contribution(prior, self.quote(1, bid="100.5", q="3")), 3)
        self.assertEqual(contribution(prior, self.quote(1, bid="99", q="3")), -2)
        self.assertEqual(contribution(prior, self.quote(1, ask="102", r="3")), 2)
        self.assertEqual(contribution(prior, self.quote(1, ask="100.5", r="3")), -3)
        self.assertEqual(contribution(prior, self.quote(1, q="3", r="1")), 2)
        self.assertEqual(contribution(prior, self.quote(1)), 0)

    def test_normalization_and_static_control(self):
        window = [self.quote(i) for i in range(20)] + [self.quote(20, q="4")]
        self.assertEqual(scores(window), (D("0.04878048780487804878048780487804878"),
                                          D("0.3333333333333333333333333333333333")))
        self.assertEqual(scores([self.quote(i, q="4") for i in range(21)]),
                         (D(0), D("0.3333333333333333333333333333333333")))

    def test_warmup_staleness_and_purge(self):
        prefix = [self.quote(i) for i in range(20)]
        self.assertIsNone(scores(prefix))
        self.assertEqual(scores(prefix + [self.quote(20, ns=5 * NANOSECONDS)]), (0, 0))
        self.assertIsNone(scores(prefix + [self.quote(20, ns=5 * NANOSECONDS + 1)]))
        self.assertIsNone(scores(prefix + [self.quote(20, segment="two")]))
        self.assertIsNone(scores(prefix + [self.quote(20, ask="100")]))

    def test_receive_order_and_future_suffix(self):
        prefix = [self.quote(i) for i in range(21)]
        for suffix in (self.quote(21, q="200"), self.quote(21, r="200")):
            replay = prefix + [suffix]
            self.assertEqual(scores(replay[:21]), (0, 0))
        self.assertIsNone(scores(prefix[:20] + [self.quote(19)]))
        self.assertIsNone(scores(prefix[:20] + [self.quote(20, ns=-1)]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
