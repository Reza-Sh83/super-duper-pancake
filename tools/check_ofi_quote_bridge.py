"""Verify shared OFI arithmetic on accepted books without running a policy."""

import argparse
from collections import deque
from decimal import Decimal as D, localcontext
import hashlib
from pathlib import Path
import runpy

from crypto_paper.data import Book, NANO, crc, load
from crypto_paper.verify import UTC, market

ORACLE = "57dc5d309e42bbe45c030340d31a13a1314c6cb45219c669125068ac690acc35"
CAPTURE = "8ffd362b49a21c859afa7a30da1cebff4f5508c9ef55b0ad9ffdb4ee94b50135"


def pinned(path, digest):
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != digest:
        raise ValueError(f"pinned file digest differs: {path.name}")
    return payload


def check(oracle_source, fixture):
    pinned(oracle_source, ORACLE)
    oracle = runpy.run_path(str(oracle_source))
    quote, contribution, scores = (oracle[key] for key in ("Quote", "contribution", "scores"))

    captured = load(pinned(fixture, CAPTURE))
    book = Book()
    book.connect(1)
    count = 0
    for index, frame in enumerate(captured["raw"], 1):
        assert book.apply(1, index, load(frame["wire"]))
        assert crc(book.sides) == captured["checks"][index - 1]["checksum"]
        count += 1
    assert count < 21  # Captured CRC excerpt provides no feature or trading evidence.

    book = Book()
    book.connect(1)
    window = deque(maxlen=21)

    def push(index, *, q="2", r="4", elapsed=None, epoch=1, snapshot=False):
        elapsed = index * 100_000_000 if elapsed is None else elapsed
        message = market(utc=UTC + elapsed, asks={"101": r}, bids={"100": q})
        message["type"] = "snapshot" if snapshot else "update"
        assert book.apply(epoch, index, message)
        assert book.fresh(UTC + elapsed)
        window.append(quote(str(epoch), index, elapsed, book.bid, book.sides["bids"][book.bid],
                            book.ask, book.sides["asks"][book.ask]))

    push(1, elapsed=0, snapshot=True)
    for index in range(2, 21):
        push(index)
    assert scores(tuple(window)) is None
    push(21, q="3", r="2", elapsed=5*NANO)
    assert contribution(window[-2], window[-1]) == 3
    with localcontext() as ctx:
        ctx.prec = 34
        expected = D(3) / D("59.5"), D(".2")
    assert scores(tuple(window)) == expected
    prior = tuple(window)
    push(22, q="3", r="2", elapsed=5*NANO)
    assert contribution(window[-2], window[-1]) == 0
    assert scores(prior) == expected

    book.invalidate()
    window.clear()
    book.connect(2)
    assert not book.apply(1, 23, market(utc=UTC + 6*NANO))
    push(24, elapsed=6*NANO, epoch=2, snapshot=True)
    assert scores(tuple(window)) is None
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("oracle", type=Path)
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    count = check(args.oracle, args.fixture)
    print(f"PASS: {count} captured CRC frames (no feature score); synthetic +3, repeated zero, "
          "five-second window, prefix stability and new-epoch warm-up.")


if __name__ == "__main__":
    main()
