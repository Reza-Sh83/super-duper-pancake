"""Offline fee-adjusted cash and best-quote paper baseline for a sealed UTC day."""

import argparse
import copy
from pathlib import Path
import sqlite3

from crypto_paper.data import D, DAY, NANO, SYMBOL, dump, load, parse_time, sha, stamp
from crypto_paper.engine import Engine, Ledger
from crypto_paper.runtime import Session, compare, digest_file, frames, verified_parts


class Blocked(ValueError):
    """The input cannot support a qualified full-day outcome."""


class TopLevelEngine(Engine):
    def match(self, oid, order, book, meta, frame):
        # Share used depth with the original book so it cannot be spent twice.
        top = copy.copy(book)
        top.sides = {"bids": {book.bid: book.sides["bids"][book.bid]},
                     "asks": {book.ask: book.sides["asks"][book.ask]}}
        super().match(oid, order, top, meta, frame)


class Baseline(Session):
    def __init__(self, run_id, start, end, ledger):
        super().__init__(None, run_id, "observe", ledger=ledger, stats=False)
        self.engine = TopLevelEngine(ledger)
        self.start, self.end = start, end
        self.requested = False
        self.max_drawdown = D(0)
        self.last_eligible = None

    def process(self, frame, obj):
        utc = frame["utc"]
        old_index = self.book.index
        super().process(frame, obj)
        if not self.start <= utc < self.end:
            return
        if self.ready(frame) and self.book.index != old_index and self.book.index == frame["idx"]:
            self.last_eligible = frame
            available = self.book.sides["bids"][self.book.bid] - self.book.used["bids"][self.book.bid]
            if self.engine.val("btc") > available:
                raise Blocked("marked position exceeds remaining displayed bid depth")
            nav, peak = self.engine.val("nav"), self.engine.val("high")
            self.max_drawdown = max(self.max_drawdown, 100 * (peak - nav) / peak)
            if not self.requested:
                self.requested = True
                # One entry request, capped by the standard Engine's initial
                # order/exposure limits. No retry or look-ahead.
                self.engine.order("baseline/entry", D(".025"), self.book, self.meta, frame)


def reconcile_baseline(session, end):
    engine, book = session.engine, session.book
    initial = D(10000)
    cash, btc, fees = initial, D(0), D(0)
    buys = sells = 0
    for _, _, kind, payload in session.ledger.sequence():
        if kind != "fill":
            continue
        fill = load(payload)
        gross, quantity, fee = (D(fill[k]) for k in ("gross", "qty", "fee"))
        if fee != gross * engine.fee or fill["fee_currency"] != "USD":
            raise Blocked("fee ledger does not reconcile")
        sign = 1 if fill["side"] == "buy" else -1
        buys += sign == 1
        sells += sign == -1
        cash -= sign * gross + fee
        btc += sign * quantity
        fees += fee
    if (cash, btc) != (engine.val("cash"), engine.val("btc")) or not session.ledger.reconcile():
        raise Blocked("paper ledger does not reconcile")
    if not buys:
        raise Blocked("no executable entry at the retained top of book")
    last = session.last_eligible
    if last is None or not session.ready(last | {"utc": end, "mono": last["mono"] + end-last["utc"]}):
        raise Blocked("missing fresh closing bid or trusted clock")
    if engine.s["orders"]:
        raise Blocked("unresolved order at the cutoff")
    if btc > book.sides["bids"][book.bid] - book.used["bids"][book.bid]:
        raise Blocked("closing position exceeds remaining displayed bid depth")
    reserve = btc * book.bid * engine.fee
    nav = cash + btc * book.bid - reserve
    if nav != engine.val("nav"):
        raise Blocked("closing marked NAV does not reconcile")
    return {"initial_usd": initial, "cash_usd": cash, "btc": btc, "nav_usd": nav,
            "fees_paid_usd": fees, "exit_fee_reserve_usd": reserve, "net_usd": nav-initial,
            "net_percent": 100*(nav/initial-1), "max_drawdown_percent": session.max_drawdown,
            "buy_fills": buys, "sell_fills": sells}


def evaluate(manifest, start):
    day = DAY * NANO
    end = start + day
    if start % day:
        raise Blocked("start must be UTC midnight")
    manifest_hash = digest_file(manifest)
    document = load(manifest.read_bytes())
    if not isinstance(document, dict) or document.get("schema_version") != 1 or "parts" not in document:
        raise Blocked("requires a sealed capture manifest and its original ledger")
    info, parts = verified_parts(manifest)
    if (not parts or info["policy"] != "observe" or info.get("state") != "DONE" or
            info.get("clock_unverified_diagnostic")):
        raise Blocked("requires a sealed, completed observe capture with verified clock")
    ledger_path = manifest.parent / "ledger.sqlite3"
    if digest_file(ledger_path) != info.get("ledger_sha256"):
        raise Blocked("sealed ledger hash differs")

    source = Ledger(ledger_path, readonly=True)
    observed = Session(None, info["run_id"], "observe", ledger=Ledger(":memory:"), stats=False)
    baseline = Baseline(info["run_id"], start, end, Ledger(":memory:"))
    next_sample = 0
    end_seen = False
    try:
        recorded = iter(source.db.execute("SELECT idx,digest FROM frames ORDER BY idx"))
        for frame in frames(manifest.parent, parts):
            utc = frame["utc"]
            if (frame["venue"] != "kraken" or frame["instrument"] != SYMBOL or
                    frame["capture_id"] != info["run_id"] or
                    next(recorded, None) != (frame["idx"], sha(dump(frame).encode()))):
                raise Blocked("source frame identity differs")
            observed.handle(frame)
            if utc >= end:
                end_seen = True
                continue
            if end_seen:
                raise Blocked("frame UTC reentered the closed interval")
            if frame["kind"] == "ws" and parse_time(frame["received_utc"]) >= end:
                raise Blocked("book evidence received after the interval cutoff")
            baseline.handle(frame)
            if utc < start:
                continue
            if frame["kind"] in {"restart", "overflow", "disconnect", "connect", "shutdown", "operator"}:
                raise Blocked("capture discontinuity or intervention within the day")
            if not observed.ready(frame):
                raise Blocked("unverified clock, missing metadata or stale book within the day")
            if frame["kind"] == "sample":
                if (utc-start)//NANO != next_sample:
                    raise Blocked("missing, duplicate or reordered sample slot")
                next_sample += 1
        if (next(recorded, None) is not None or not source.reconcile() or
                not observed.ledger.reconcile() or not compare(source, observed.ledger)["equal"] or
                dump(source.state) != dump(observed.ledger.state)):
            raise Blocked("sealed ordered replay does not reconcile")
        if next_sample != DAY or not end_seen:
            raise Blocked("incomplete UTC day")
        result = reconcile_baseline(baseline, end)
        if (digest_file(manifest) != manifest_hash or digest_file(ledger_path) != info["ledger_sha256"] or
                any(digest_file(manifest.parent / name) != digest for name, digest in info["parts"].items())):
            raise Blocked("retained source changed during replay")
        cash = {"initial_usd": D(10000), "nav_usd": D(10000), "fees_paid_usd": D(0),
                "exit_fee_reserve_usd": D(0), "net_usd": D(0), "net_percent": D(0),
                "max_drawdown_percent": D(0)}
        return {"status": "PASS", "start": stamp(start), "end_exclusive": stamp(end),
                "manifest_sha256": manifest_hash, "sampled_seconds": next_sample,
                "cash_control": cash, "best_quote_paper": result,
                "target_50_percent_candidate": result["net_percent"] >= 50}
    finally:
        baseline.close()
        observed.close()
        source.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--day", required=True, help="UTC date in YYYY-MM-DD form")
    args = parser.parse_args()
    try:
        result = evaluate(args.manifest, parse_time(args.day + "T00:00:00Z"))
    except (OSError, ValueError, KeyError, ArithmeticError, sqlite3.Error) as error:
        print(dump({"status": "BLOCKED", "reason": str(error)}))
        raise SystemExit(2) from None
    print(dump(result))


if __name__ == "__main__":
    main()
