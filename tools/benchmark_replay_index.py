"""Experimental end-to-end sealed replay benchmark; never changes production code.

The index exists only in the rebuilt :memory: ledger. Input build, segment,
payload, committed-frame, ordered-event and final-account checks stay intact.
Run sequentially before a capture, never as an operational acceptance receipt.
"""
import argparse
from collections import Counter
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import sys
import time

# Direct invocation works from the repository without installation.
PROJECT = Path(__file__).resolve().parents[1]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from crypto_paper import capture_report as projector
from crypto_paper.data import dump, parse_time, sha
from crypto_paper.engine import Ledger
from crypto_paper.runtime import code_hashes, digest_file, verified_parts, write_json


def audit(ledger):
    """Hash exact row order, without using the financial calculation helper."""
    all_rows, financial, committed = (hashlib.sha256() for _ in range(3))
    counts = Counter()
    financial_count = frame_count = 0
    for row in ledger.sequence():
        encoded = (dump(list(row))+'\n').encode()
        all_rows.update(encoded)
        counts[row[2]] += 1
        # Full ordered hash above includes even nonfinancial provenance.
        if row[2] not in ('metadata', 'reject'):
            financial.update(encoded)
            financial_count += 1
    for row in ledger.db.execute('SELECT idx,digest FROM frames ORDER BY idx'):
        committed.update((dump(list(row))+'\n').encode())
        frame_count += 1
    return dict(ordered_events_sha256=all_rows.hexdigest(), event_count=sum(counts.values()),
                event_counts=dict(counts), financial_events_sha256=financial.hexdigest(),
                financial_event_count=financial_count,
                financial_selection='all ordered events except metadata and reject',
                committed_frames_sha256=committed.hexdigest(), frame_count=frame_count,
                final_account=ledger.state, final_account_sha256=sha(dump(ledger.state).encode()),
                reconciled=ledger.reconcile())


@contextmanager
def experimental_ledgers(indexed, summaries):
    """Inject only a physical in-memory index; restore the factory on failure."""
    original = projector.Ledger

    class AuditedLedger(Ledger):
        def __init__(self, path, *, readonly=False):
            super().__init__(path, readonly=readonly)
            self.label = 'rebuilt' if str(path) == ':memory:' else 'source'
            self.done = False
            if indexed and self.label == 'rebuilt':
                self.db.execute('CREATE INDEX experimental_events_frame ON events(frame)')

        def close(self):
            if not self.done:
                summaries[self.label] = audit(self)
                self.done = True
                super().close()

    projector.Ledger = AuditedLedger
    try:
        yield
    finally:
        projector.Ledger = original


def run_variant(manifest, start, end, indexed):
    summaries = {}
    began = time.perf_counter()
    with experimental_ledgers(indexed, summaries):
        snapshot, metrics = projector.snapshot_from_capture(manifest, start, end)
    elapsed = time.perf_counter()-began
    if set(summaries) != {'source', 'rebuilt'}:
        raise ValueError('both source and rebuilt ledger audits required')
    source, rebuilt = summaries['source'], summaries['rebuilt']
    if not source['reconciled'] or not rebuilt['reconciled'] or source != rebuilt:
        raise ValueError('ordered event/frame or final-account audit mismatch')
    return dict(variant='transient_events_frame_index' if indexed else 'unindexed',
                end_to_end_seconds=elapsed,
                timing_scope='complete unchanged snapshot_from_capture call, including sealed verification, replay, report projection and close-time audits',
                ledger_audit=rebuilt, source_audit=source,
                ordered_events_equal=True, ordered_financial_events_equal=True,
                final_account_equal=True, snapshot_sha256=sha(dump(snapshot).encode()),
                metrics_sha256=sha(dump(metrics).encode()),
                snapshot_count=len(snapshot['snapshots']), readback=metrics['readback'])


def benchmark(manifest, start, end):
    if start >= end:
        raise ValueError('start must precede end')
    manifest = Path(manifest)
    info, parts = verified_parts(manifest)
    source_paths = [manifest, manifest.parent/'ledger.sqlite3', *parts]
    before = {str(p):digest_file(p) for p in source_paths}
    build = code_hashes()
    variants = [run_variant(manifest,start,end,indexed) for indexed in (False,True)]
    after = {str(p):digest_file(p) for p in source_paths}
    if before != after or code_hashes() != build:
        raise ValueError('source input or recorded-build code changed during experiment')
    baseline, candidate = variants
    for key in ('ledger_audit','snapshot_sha256','metrics_sha256','snapshot_count','readback'):
        if baseline[key] != candidate[key]:
            raise ValueError(f'baseline/candidate result differs: {key}')
    return dict(schema_version='experimental-replay-index-v1', source_run_id=info['run_id'],
                source_code_hashes=build, source_manifest_sha256=before[str(manifest)],
                candidate_script_sha256=digest_file(Path(__file__).resolve()),
                source_input_hashes_before=before, source_input_hashes_after=after,
                source_unchanged=True, source_input_bytes=sum(p.stat().st_size for p in source_paths),
                variants=variants,
                end_to_end_speed_ratio=baseline['end_to_end_seconds']/candidate['end_to_end_seconds'],
                identical_ordered_events=True, identical_financial_events=True,
                identical_final_account=True, identical_snapshot_and_metrics=True,
                nonzero_financial_events_validated=bool(baseline['ledger_audit']['financial_event_count']),
                financial_validation_scope=('nonzero recorded financial events' if baseline['ledger_audit']['financial_event_count']
                                            else 'ZERO_FINANCIAL_EVENTS: invariance only; no nonzero fee/fill validation in this capture'),
                index_scope='rebuilt in-memory ledger only; source readonly ledger and production implementation unchanged',
                operational_acceptance=False, strategy_return_improvement=False,
                limitations=['one sequential baseline-then-candidate pair; cache/order and host load can affect timing',
                             'source capture may contain no fills; nonzero fee/fill behavior requires synthetic fixture',
                             'input bytes measured; transient memory peak not instrumented',
                             'diagnostic build verification is not independent operational acceptance'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--start',required=True)
    p.add_argument('--end',required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():
        raise ValueError('benchmark receipt already exists')
    result=benchmark(a.manifest,parse_time(a.start),parse_time(a.end))
    # Exclusive creation prevents accidental replacement of a prior receipt.
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x',encoding='utf-8') as stream:
        stream.write(dump(result)+'\n')
        stream.flush()
        os.fsync(stream.fileno())


if __name__ == '__main__':
    main()
