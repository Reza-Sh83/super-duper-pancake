"""Sealed capture to committed-ledger dry-run reports. No pilot or delivery side effects."""
import argparse
from pathlib import Path

from .data import NANO, dump, load, parse_time, sha
from .engine import Ledger
from .diagnostic import DiagnosticBook
from .pilot_report import HOUR, project
from .runtime import Session, compare, digest_file, frames, verified_parts


def snapshot_from_capture(manifest, start, end):
    info, parts = verified_parts(manifest)
    if info.get('state') == 'COLLECTING' or not parts:
        raise ValueError('sealed nonempty capture required')
    ledger_path = manifest.parent/'ledger.sqlite3'
    if info.get('ledger_sha256') != digest_file(ledger_path):
        raise ValueError('sealed ledger hash mismatch')
    rebuilt = Session(None, info['run_id'], info['policy'], ledger=Ledger(':memory:'))
    source = Ledger(ledger_path, readonly=True)
    diagnostic = DiagnosticBook()
    snapshots, fills, slots = [], [], {}
    good = errors = connects = disconnects = book_samples = 0
    mark_received = None
    first_mono = last_mono = None
    try:
        for f in frames(manifest.parent, parts):
            if f['capture_id'] != info['run_id']:
                raise ValueError('capture identity mismatch')
            digest = sha(dump(f).encode())
            saved = source.db.execute('SELECT digest FROM frames WHERE idx=?',(f['idx'],)).fetchone()
            if saved != (digest,):
                raise ValueError('committed frame digest mismatch')
            prior = rebuilt.book.index
            rebuilt.handle(f)
            diagnostic.handle(f)
            if f['kind'] == 'run_begin': first_mono = f['mono']
            last_mono = f['mono']
            if f['kind'] == 'connect': connects += 1
            if f['kind'] == 'disconnect': disconnects += 1
            if rebuilt.book.index != prior and rebuilt.book.index == f['idx']:
                good += 1
                mark_received = parse_time(f['received_utc'])
            for kind, data in rebuilt.ledger.db.execute('SELECT kind,payload FROM events WHERE frame=?',(f['idx'],)):
                event = load(data)
                if kind == 'reject' and 'checksum' in event.get('reason',''): errors += 1
                if kind == 'fill':
                    fills.append(dict(utc=event['filled_utc'],received_utc=parse_time(f['received_utc']),
                                      frame=f['idx'],fee_usd=event['fee']))
            if f['kind'] == 'sample' and start <= f['utc'] < end:
                slot = (f['utc']-start)//NANO
                slots[slot] = slots.get(slot,True) and bool(rebuilt.ready(f))
                book_samples += bool(rebuilt.book.fresh(f['utc']))
            state, book = rebuilt.engine.s, rebuilt.book
            snapshots.append(dict(frame=f['idx'],utc=f['utc'],received_utc=parse_time(f['received_utc']),
                                  cash=state['cash'],btc=state['btc'],last_observed_nav=state['nav'],
                                  mark_utc=book.event_ns,mark_received_utc=mark_received,
                                  bid=str(book.bid) if book.state == 'READY' else None,
                                  book_valid=book.state == 'READY',clock_valid=bool(rebuilt.ready(f)),
                                  journal_reconciled=True))
        cursor = snapshots[-1]['frame']
        if source.db.execute('SELECT count(*),max(idx) FROM frames').fetchone() != (cursor,cursor):
            raise ValueError('ledger/raw cursor mismatch')
        if (not source.reconcile() or not rebuilt.ledger.reconcile() or
                not compare(source,rebuilt.ledger)['equal'] or dump(source.state) != dump(rebuilt.ledger.state)):
            raise ValueError('ledger replay reconciliation failed')
        expected = (end-start)//NANO
        ready = sum(slots.values())
        coverage = dict(ready=ready,nonready=len(slots)-ready,missing=expected-len(slots))
        # This adapter is deliberately observation-only until multi-arm ledgers are reviewed.
        if info['policy'] != 'observe':
            raise ValueError('only observe ledger adapter reviewed for dry-run use')
        snap = dict(schema_version='pilot-snapshot-v1',mode='dry_run',run_id=info['run_id'],
                    policy='observe',scenario='base',kind='six_hour',pilot_start=start,
                    interval_start=start,interval_end=end,revision=0,snapshots=snapshots,
                    committed_frame=cursor,coverage=coverage,fills=fills,opening_peak='10000',
                    code_hashes=info['code_hashes'],config_hash=sha(dump({'policy':info['policy']}).encode()),
                    manifest_hash=digest_file(manifest),unresolved_gaps=['diagnostic interval'],
                    integrity='PASS',replay='PASS',risk_violations=[],locks=[],dust='0',
                    decisions={'status':'UNAVAILABLE'},reconciliation={'status':'PASS','scope':'exact sealed replay'},
                    paired_baselines={'pair_count':0,'missing':1},completed_work=['Sealed capture readback and ledger replay'])
        metrics = dict(good_book_frames=good,checksum_errors=errors,connects=connects,
                       reconnects=max(0,connects-1),disconnects=disconnects,
                       capture_index_gaps=0,exchange_sequence_gaps='UNAVAILABLE: feed has no sequence counter',
                       duration_monotonic_sec=(last_mono-first_mono)/NANO if first_mono is not None else 0,
                       raw_bytes=sum(p.stat().st_size for p in parts),parts=info['parts'],
                       source_ledger_sha256=info['ledger_sha256'],readback='PASS',coverage=coverage)
        metrics.update(capture_coverage=rebuilt.metrics(),
                       diagnostic_observer=diagnostic.metrics(),
                       checksum_valid_fresh_book_samples=book_samples,
                       clock_status='UNVERIFIED' if info.get('clock_unverified_diagnostic') or info.get('state') == 'DIAGNOSTIC' else 'SEE_CLOCK_FRAMES')
        return snap, metrics
    finally:
        source.close()
        rebuilt.close()


def capture_report(manifest, start, end, generated):
    if end-start != 6*HOUR or generated < end:
        raise ValueError('completed six-hour diagnostic report interval required')
    snap, metrics = snapshot_from_capture(manifest,start,end)
    result = project(snap,generated)
    reasons = []
    if not snap['snapshots'] or snap['snapshots'][0]['utc'] >= start: reasons.append('OPENING_HISTORY_MISSING')
    if snap['coverage']['missing']: reasons.append('INTERVAL_INCOMPLETE')
    if (metrics['clock_status'] == 'UNVERIFIED' or
            not all(x['clock_valid'] for x in snap['snapshots'] if start <= x['utc'] < end)):
        reasons.append('CLOCK_UNVERIFIED')
    # Diagnostic cash balances do not establish a validated trading return.
    if reasons:
        for key in ('interval_net','inception_net'):
            result[key] = dict(usd=None,percent=None,reason=','.join(reasons))
        result['observed_max_drawdown_percent'] = None
        result['drawdown_current'] = 'UNKNOWN'
    result.update(validation_reasons=reasons,pilot_started=False,capture_metrics=metrics,
                  next_action='Resolve clock, acceptance, storage and reporting gates; independent adapter review')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--start',required=True)
    p.add_argument('--end',required=True)
    p.add_argument('--generated-at',required=True)
    p.add_argument('--out',type=Path,required=True)
    a = p.parse_args()
    result = capture_report(a.manifest,parse_time(a.start),parse_time(a.end),parse_time(a.generated_at))
    with a.out.open('x',encoding='utf-8') as stream: stream.write(dump(result)+'\n')


if __name__ == '__main__': main()
