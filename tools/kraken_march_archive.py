"""Verify Capture's canonical March XBTUSD hourly archive slices for offline research."""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path


HOUR = 3600


@dataclass(frozen=True)
class Slice:
    start: str
    end: str
    digest: str

    def grid(self):
        start, end = (int(datetime.fromisoformat(value).replace(tzinfo=timezone.utc).timestamp())
                      for value in (self.start, self.end))
        return range(start, end, HOUR)


# Capture 4d1f286 binds these two source slices. Validation has a separate gate.
DEVELOPMENT_WARMUP = Slice("2026-03-02T22:00", "2026-03-04T00:00",
                           "7362346f6f5aa10d8d3a13230afc824f9af205b26f492e0b15f3e6d3e2c6cb1c")
DEVELOPMENT = Slice("2026-03-04T00:00", "2026-03-16T00:00",
                    "06752e942790711b27028a6ba4748ab1918f98966b55faabc0fdbe0b2821b8d2")


def canonical(rows):
    return (json.dumps(rows, separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii")


def decoded_rows(payload, binding):
    if hashlib.sha256(payload).hexdigest() != binding.digest:
        raise ValueError("archive slice SHA-256 mismatch")
    rows = json.loads(payload)
    if not isinstance(rows, list):
        raise ValueError("expected canonical OHLCVT row array")
    if len(rows) != len(binding.grid()) or canonical(rows) != payload:
        raise ValueError("archive slice size or canonical form mismatch")
    model_rows = []
    for timestamp, row in zip(binding.grid(), rows):
        if (not isinstance(row, list) or len(row) != 7
                or not all(type(field) is str for field in row)):
            raise ValueError("expected seven original OHLCVT CSV string columns")
        if row[0] != str(timestamp):
            raise ValueError("missing, duplicate, unordered or off-grid UTC hour")
        if not row[6].isascii() or not row[6].isdecimal():
            raise ValueError("invalid trade count")
        try:
            opening, high, low, close, volume = map(Decimal, row[1:6])
        except InvalidOperation as error:
            raise ValueError("invalid archive decimal") from error
        if (not all(value.is_finite() for value in (opening, high, low, close, volume))
                or not (0 < low <= min(opening, close) <= max(opening, close) <= high)
                or volume < 0):
            raise ValueError("invalid OHLCVT")
        # The frozen signal/model consumes only timestamp and four OHLC columns.
        model_rows.append([timestamp, *row[1:5]])
    return model_rows


def read_development(warmup: Path, evaluation: Path):
    return (decoded_rows(warmup.read_bytes(), DEVELOPMENT_WARMUP)
            + decoded_rows(evaluation.read_bytes(), DEVELOPMENT))
