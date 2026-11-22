"""Read-only private Kraken evidence inventory. Output contains private paths."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from crypto_paper.diagnostic import DiagnosticBook
from crypto_paper.runtime import digest_file, frames, payload


def audit(manifest):
    info = json.loads(manifest.read_bytes())
    root = manifest.parent
    parts = []
    for name, digest in sorted(info['parts'].items()):
        part = root / name
        if part.is_symlink() or part.resolve().parent != (root / 'raw').resolve():
            raise ValueError('unexpected raw part path')
        if digest_file(part) != digest:
            raise ValueError('raw part hash mismatch')
        parts.append(part)

    observer = DiagnosticBook()
    kinds, channels, depth = Counter(), Counter(), Counter()
    first_book = last_book = first_receive = last_receive = None
    previous_wire = {}
    largest_wire_gap = 0
    trade_rows = 0
    for frame in frames(root, parts):
        kinds[frame['kind']] += 1
        before = observer.good
        observer.handle(frame)
        if frame['kind'] != 'ws':
            continue
        obj = payload(frame)
        if not isinstance(obj, dict):
            channels['non-object'] += 1
            continue
        channel = obj.get('channel', 'control')
        channels[channel] += 1
        if channel == 'trade':
            trade_rows += len(obj.get('data', ()))
        received = frame['received_monotonic_ns']
        epoch = frame['connection_epoch']
        if epoch in previous_wire:
            largest_wire_gap = max(largest_wire_gap, received - previous_wire[epoch])
        previous_wire[epoch] = received
        if observer.good == before:
            continue
        depth[(len(observer.book.sides['bids']), len(observer.book.sides['asks']))] += 1
        exchange = obj['data'][0]['timestamp']
        first_book = first_book or exchange
        last_book = exchange
        first_receive = first_receive or frame['received_utc']
        last_receive = frame['received_utc']

    planned = info.get('duration_sec')
    return {
        'state': info['state'],
        'declared_seconds': planned,
        'missing_sample_slots': max(0, planned - observer.samples) if planned else None,
        'manifest_sha256': digest_file(manifest),
        'raw_stream_sha256': hashlib.sha256(''.join(info['parts'][n] for n in sorted(info['parts'])).encode()).hexdigest(),
        'raw_parts': len(parts),
        'raw_bytes': sum(part.stat().st_size for part in parts),
        'frames': dict(kinds), 'channels': dict(channels), 'trade_rows': trade_rows,
        'first_book_exchange': first_book, 'last_book_exchange': last_book,
        'first_book_receive': first_receive, 'last_book_receive': last_receive,
        'largest_same_epoch_ws_gap_ms': largest_wire_gap / 1_000_000,
        'depth': {f'{b}/{a}': count for (b, a), count in sorted(depth.items())},
        'book': observer.metrics(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('private_root', type=Path)
    parser.add_argument('out', type=Path)
    args = parser.parse_args()
    grouped = {}
    for path in sorted(args.private_root.rglob('manifest.json')):
        data = json.loads(path.read_bytes())
        if data.get('schema_version') == 1 and isinstance(data.get('parts'), dict) and data['parts']:
            key = tuple(sorted(data['parts'].items()))
            grouped.setdefault(key, []).append(path)
    report = []
    for paths in grouped.values():
        row = audit(paths[0])
        row['locations'] = [str(p.relative_to(args.private_root)) for p in paths]
        report.append(row)
    with args.out.open('x') as sink:
        json.dump(report, sink, sort_keys=True, indent=2)
        sink.write('\n')
    print(f'Inspected {len(report)} distinct raw streams from {sum(map(len, grouped.values()))} manifest locations')


if __name__ == '__main__':
    main()
