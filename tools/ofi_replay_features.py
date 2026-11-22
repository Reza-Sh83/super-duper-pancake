"""Isolated offline feature transcript for the frozen OFI-L2-01 contract."""

from collections import deque
import runpy

from crypto_paper.data import NANO
from crypto_paper.runtime import Session
from tools.check_ofi_quote_bridge import ORACLE, pinned


class FeatureSession(Session):
    """Verify native frames in observe mode and record the causal score prefix."""

    def __init__(self, ledger, run_id, start, end, oracle_path):
        if start % (86400 * NANO) or end - start != 86400 * NANO:
            raise ValueError("expected one complete UTC day")
        pinned(oracle_path, ORACLE)
        oracle = runpy.run_path(str(oracle_path))
        super().__init__(None, run_id, "observe", ledger=ledger, stats=False)
        self.start, self.end = start, end
        self.quote, self.scores = oracle["Quote"], oracle["scores"]
        self.window = deque(maxlen=21)
        self.segment = 0
        self.last_second = None
        self.closed = False
        self.observations = []

    def clear_feature(self):
        if self.window:
            self.window.clear()
            self.segment += 1

    def process(self, frame, obj):
        utc = frame["utc"]
        if self.closed or utc >= self.end:
            self.closed = True
            self.clear_feature()
            return
        metadata = self.meta
        # A newly received update must not hide the period in which the
        # preceding quote was no longer valid.
        if self.window and not self.ready(frame):
            self.clear_feature()
        super().process(frame, obj)
        if (utc < self.start or not self.ready(frame) or metadata != self.meta
                or frame["kind"] in {"connect", "restart"}):
            self.clear_feature()
        if utc < self.start or self.book.index != frame["idx"] or not self.ready(frame):
            return
        bid, ask = self.book.bid, self.book.ask
        self.window.append(self.quote(
            str(self.segment), frame["idx"], frame["mono"], bid, self.book.sides["bids"][bid],
            ask, self.book.sides["asks"][ask],
        ))
        scores = self.scores(tuple(self.window))
        second = utc // NANO
        if scores is None or (self.last_second is not None and second <= self.last_second):
            return
        self.last_second = second
        self.observations.append({
            "receive_index": frame["idx"], "utc": utc, "monotonic_ns": frame["mono"],
            "segment": self.segment, "first_index": self.window[0].receive_index,
            "ofi": scores[0], "static_imbalance": scores[1],
        })
