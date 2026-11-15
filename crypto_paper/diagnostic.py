"""Clock-independent feed diagnostics. Never grants production readiness or orders."""
from collections import Counter

from .data import Book, NANO
from .runtime import payload


class DiagnosticBook:
    def __init__(self):
        self.book = Book()
        self.good = self.errors = self.samples = self.available = 0
        self.last_book_mono = None
        self.pending_recovery = None
        self.recoveries_ms = []
        self.disconnects = Counter()
        self.clock_failures = 0

    def handle(self, frame):
        kind = frame['kind']
        if kind == 'connect':
            self.book.connect(frame['connection_epoch'])
        elif kind in ('disconnect','overflow','shutdown','restart'):
            self.book.invalidate()
            self.last_book_mono = None
            if kind == 'disconnect':
                self.disconnects[frame.get('origin','unclassified')] += 1
                self.pending_recovery = frame.get('force_mono',frame['mono'])
        elif kind == 'clock':
            # Count rejected references without modifying the diagnostic book.
            from .data import D
            values = [D(v) for v in frame['offset_ms']]
            median = sorted(values)[len(values)//2] if values else None
            self.clock_failures += not (len(values) >= 3 and abs(median) <= 500 and max(values)-min(values) <= 250)
        elif kind == 'ws' and frame['connection_epoch'] == self.book.epoch:
            obj = payload(frame)
            if isinstance(obj,dict) and obj.get('channel') == 'book':
                try:
                    accepted = self.book.apply(frame['connection_epoch'],frame['idx'],obj)
                except (ValueError,KeyError,TypeError,ArithmeticError):
                    self.errors += 1
                else:
                    if accepted:
                        self.good += 1
                        self.last_book_mono = frame['received_monotonic_ns']
                        if self.pending_recovery is not None:
                            self.recoveries_ms.append((frame['mono']-self.pending_recovery)/1_000_000)
                            self.pending_recovery = None
        elif kind == 'sample':
            self.samples += 1
            self.available += (self.book.state == 'READY' and self.last_book_mono is not None and
                               0 <= frame['mono']-self.last_book_mono <= 2*NANO)

    def metrics(self):
        return dict(good_book_frames=self.good,book_validation_errors=self.errors,
                    sampled_seconds=self.samples,checksum_book_available_seconds=self.available,
                    checksum_book_available_percent=100*self.available/self.samples if self.samples else 0,
                    rejected_clock_frames=self.clock_failures,disconnects_by_origin=dict(self.disconnects),
                    recovery_to_crc_book_ms=self.recoveries_ms,
                    recovery_scope='monotonic disconnect-to-checksum-book; not operational READY',
                    utc_verified=False,production_readiness_granted=False)
