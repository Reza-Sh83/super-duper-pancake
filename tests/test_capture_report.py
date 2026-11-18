"""Synthetic sealed-ledger integration tests; no network or observed profits."""
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

from crypto_paper.capture_report import capture_report
from crypto_paper.data import NANO, dump, load, sha
from crypto_paper.engine import Ledger
from crypto_paper.pilot_report import HOUR
from crypto_paper.runtime import Capture, Session, digest_file, manifest
from crypto_paper.__main__ import collect, main
from crypto_paper.verify import META, market

T = 1767225600*NANO


class CaptureReportTests(unittest.TestCase):
    def fixture(self, root):
        out = root/'capture'; out.mkdir()
        session = Session(out,'synthetic','observe')
        cap = Capture(out,'synthetic')
        for kind,utc,fields in [('clock',T,{'offset_ms':[]}),
                                ('run_begin',T,{'duration':600}),
                                ('sample',T+NANO,{}),
                                ('shutdown',T+600*NANO,{})]:
            session.handle(cap.put(kind,utc=utc,mono=utc-T+NANO,**fields))
        cap.close(); session.close()
        manifest(out,'synthetic','observe',T,state='DIAGNOSTIC')
        return out/'manifest.json'

    def report(self, path):
        return capture_report(path,T+600*NANO-6*HOUR,T+600*NANO,T+601*NANO)

    def test_sealed_readback_and_missing_interval_are_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=self.fixture(Path(tmp))
            before={p:p.read_bytes() for p in path.parent.rglob('*') if p.is_file()}
            r=self.report(path)
            self.assertEqual(r['replay'],'PASS')
            self.assertEqual(r['capture_metrics']['readback'],'PASS')
            self.assertIsNone(r['interval_net']['usd'])
            self.assertIsNone(r['observed_max_drawdown_percent'])
            self.assertEqual(r['coverage']['expected'],21600)
            self.assertEqual(r['coverage']['missing'],21599)
            self.assertIn('CLOCK_UNVERIFIED',r['validation_reasons'])
            self.assertFalse(r['pilot_started']); self.assertFalse(r['real_alert_sent'])
            self.assertEqual(before,{p:p.read_bytes() for p in before})

    def test_marked_ledger_reconciles_canonical_account_and_respects_diagnostic_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            session = Session(out, 'marked', 'observe')
            capture = Capture(out, 'marked')
            for kind, offset, wire, fields in (
                ('clock', 0, b'', {'offset_ms': ['0', '0', '0']}),
                ('connect', 0, b'', {}),
                ('ws', 0, dump({'channel': 'instrument', 'data': {
                    'pairs': [META | {'symbol': 'BTC/USD'}]}}).encode(), {}),
                ('ws', 0, dump(market(utc=T)).encode(), {}),
                ('sample', 1, b'', {}),
            ):
                session.handle(capture.put(kind, wire, epoch=1,
                                           utc=T+offset*NANO, mono=offset*NANO, **fields))
            self.assertEqual(session.ledger.state['mark_ns'], T)
            capture.close()
            session.close()
            manifest(out, 'marked', 'observe', T, state='DONE',
                     clock_unverified_diagnostic=True)
            result = capture_report(out/'manifest.json', T+NANO, T+NANO+6*HOUR, T+NANO+6*HOUR)
            self.assertEqual(result['replay'], 'PASS')
            self.assertIn('CLOCK_UNVERIFIED', result['validation_reasons'])
            self.assertIsNone(result['interval_net']['usd'])
            self.assertIsNone(result['observed_max_drawdown_percent'])

    def test_raw_tamper_and_collecting_manifest_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=self.fixture(Path(tmp)); info=load(path.read_bytes())
            info['state']='COLLECTING'; path.write_text(dump(info))
            with self.assertRaisesRegex(ValueError,'sealed'): self.report(path)
            info['state']='DIAGNOSTIC'; path.write_text(dump(info))
            part=path.parent/'raw/000001.jsonl'; part.write_bytes(part.read_bytes()+b'bad')
            with self.assertRaisesRegex(ValueError,'invalid manifest'): self.report(path)

    def test_resealed_frame_change_does_not_match_committed_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=self.fixture(Path(tmp)); part=path.parent/'raw/000001.jsonl'
            lines=part.read_bytes().splitlines(); f=load(lines[0]); f['offset_ms']=['0','0','0']
            lines[0]=dump(f).encode(); part.write_bytes(b'\n'.join(lines)+b'\n')
            info=load(path.read_bytes()); info['parts']['raw/000001.jsonl']=digest_file(part)
            path.write_text(dump(info))
            with self.assertRaisesRegex(ValueError,'committed frame digest'): self.report(path)

    def test_resealed_account_change_does_not_match_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=self.fixture(Path(tmp)); ledger=Ledger(path.parent/'ledger.sqlite3')
            ledger.db.execute('INSERT OR REPLACE INTO account VALUES (1,?)',(dump({'cash':'99999'}),))
            ledger.close()
            info=load(path.read_bytes()); info['ledger_sha256']=digest_file(path.parent/'ledger.sqlite3')
            path.write_text(dump(info))
            with self.assertRaisesRegex(ValueError,'reconciliation'): self.report(path)

    def test_diagnostic_mode_is_not_a_paper_option(self):
        with patch('sys.argv',['crypto_paper','paper','--duration-sec','600','--out','unused',
                               '--clock-unverified-diagnostic']):
            with self.assertRaises(SystemExit) as exc: main()
            self.assertEqual(exc.exception.code,2)

    def test_rotation_and_capacity_stop_preserve_readback(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'run'; out.mkdir()
            s=Session(out,'synthetic','observe'); cap=Capture(out,'synthetic')
            try:
                s.handle(cap.put('run_begin',utc=T,mono=NANO,duration=600))
                # Exercise time segmentation without allocating a large file.
                s.handle(cap.put('sample',utc=T+NANO,mono=3601*NANO))
                self.assertEqual(len(list((out/'raw').glob('*.jsonl'))),2)
                before={p:p.read_bytes() for p in (out/'raw').glob('*.jsonl')}
                with patch('crypto_paper.runtime.shutil.disk_usage',return_value=SimpleNamespace(free=2048*1024**2)):
                    with self.assertRaisesRegex(OSError,'safety disk threshold'):
                        cap.put('sample',utc=T+2*NANO,mono=3602*NANO)
                self.assertEqual(cap.idx,2)
                self.assertEqual(before,{p:p.read_bytes() for p in before})
            finally:
                cap.close(); s.close()
            manifest(out,'synthetic','observe',T,state='DIAGNOSTIC')
            result=self.report(out/'manifest.json')
            self.assertEqual(result['capture_metrics']['readback'],'PASS')
            self.assertEqual(len(result['capture_metrics']['parts']),2)

    def test_diagnostic_retains_clock_failure_but_not_storage_failure(self):
        for problem in ('independent UTC reference rejected: []','local SQLite close/reopen rejected: test'):
            with self.subTest(problem=problem), tempfile.TemporaryDirectory() as tmp:
                args=SimpleNamespace(out=Path(tmp)/'run',resume=False,duration_sec=600,
                                     force_reconnect_at_sec=None,command='capture',
                                     clock_unverified_diagnostic=True)
                calls=[]
                async def feed(session, cap, duration, force):
                    calls.append(duration)
                    self.assertEqual(session.policy,'observe')
                    self.assertFalse(session.clock)
                    return 'DONE','synthetic bounded transport'
                with patch('crypto_paper.__main__.preflight',return_value=[problem]), \
                     patch('crypto_paper.__main__.live',side_effect=feed):
                    self.assertEqual(collect(args),1)
                info=load((args.out/'manifest.json').read_bytes())
                self.assertEqual(info['host']['status'],'BLOCKED')
                self.assertEqual(calls,[600] if problem.startswith('independent') else [])
                self.assertEqual(info['state'],'DIAGNOSTIC' if calls else 'BLOCKED')


if __name__ == '__main__': unittest.main()
