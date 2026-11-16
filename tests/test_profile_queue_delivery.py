"""Synthetic profiler checks; real filesystem durability calls remain enabled."""
from pathlib import Path
import os
import sqlite3
import tempfile
import unittest
from threading import Event
from types import SimpleNamespace
from unittest.mock import patch

from crypto_paper.data import D, NANO, load
from crypto_paper.engine import Engine
from crypto_paper.verify import UTC, META, book_at
from tools import replay_queue_load as harness
from tools.benchmark_replay_index import audit
from tools.profile_queue_delivery import StageProfile, profiling, run, synthetic_source


class ProfileTests(unittest.TestCase):
    def test_stages_preserve_real_write_fsync_and_full_commit(self):
        original_sync=os.fsync
        profile=StageProfile()
        with tempfile.TemporaryDirectory() as tmp, patch.object(os,'fsync',wraps=original_sync) as sync:
            with profiling(profile):
                state=harness.DriverState(); out=Path(tmp)
                cap=harness.MeasuredCapture(out,'synthetic',state)
                session=harness.MeasuredSession(out,'synthetic',state)
                try:
                    frame=cap.put('sample',utc=UTC,mono=0)
                    session.handle(frame)
                    self.assertEqual(session.ledger.db.execute('PRAGMA synchronous').fetchone(),(2,))
                    self.assertEqual(session.ledger.db.execute('PRAGMA journal_mode').fetchone(),('persist',))
                    self.assertEqual(load((out/'raw/000001.jsonl').read_bytes())['idx'],1)
                finally:
                    cap.close(); session.close()
            self.assertEqual(sync.call_count,1)
        stages=profile.summary()
        for name in ('capture_write','capture_flush','capture_fsync','capture_total','session_total','sqlite_commit'):
            self.assertEqual(stages[name]['count'],1)
            self.assertGreaterEqual(stages[name]['total_ns'],0)
        self.assertFalse(profile.active); self.assertFalse(profile.session_active)

    def test_exception_restores_factories_and_measures_failed_stage(self):
        original=(Path.open,sqlite3.connect,harness.MeasuredCapture,harness.MeasuredSession,os.fsync,harness.producer)
        profile=StageProfile()
        with self.assertRaisesRegex(RuntimeError,'synthetic failure'):
            with profiling(profile):
                profile.measure('failure',lambda: (_ for _ in ()).throw(RuntimeError('synthetic failure')))
        self.assertEqual(original,(Path.open,sqlite3.connect,harness.MeasuredCapture,harness.MeasuredSession,os.fsync,harness.producer))
        self.assertEqual(profile.summary()['failure']['count'],1)

    def test_exclusive_candidate_keeps_full_durability_and_economic_events(self):
        variants=[]
        for exclusive in (False,True):
            with tempfile.TemporaryDirectory() as tmp, profiling(StageProfile(),exclusive):
                session=harness.MeasuredSession(Path(tmp),'synthetic',harness.DriverState())
                ledger=session.ledger; engine=Engine(ledger)
                try:
                    self.assertEqual(ledger.db.execute('PRAGMA synchronous').fetchone(),(2,))
                    self.assertEqual(ledger.db.execute('PRAGMA journal_mode').fetchone(),('persist',))
                    self.assertEqual(ledger.db.execute('PRAGMA locking_mode').fetchone(),('exclusive' if exclusive else 'normal',))
                    frame=dict(idx=1,utc=UTC,mono=0)
                    with ledger.transaction(1,'one'):
                        engine.order('buy',D('.1'),book_at(asks={'100':'1'}),META,frame)
                    with ledger.transaction(2,'two'):
                        engine.on_book(book_at(2,asks={'100':'1'}),META,frame|{'idx':2,'utc':UTC+NANO,'mono':NANO})
                        engine.order('sell',D('0'),book_at(2,asks={'100':'1'}),META,frame|{'idx':2,'mono':NANO})
                    with ledger.transaction(3,'three'):
                        engine.on_book(book_at(3,asks={'100':'1'},bids={'99.9':'1'}),META,frame|{'idx':3,'utc':UTC+2*NANO,'mono':2*NANO})
                    fills=[load(p) for _,_,kind,p in ledger.sequence() if kind=='fill']
                    self.assertEqual([x['side'] for x in fills],['buy','sell'])
                    self.assertEqual(sum(D(x['fee']) for x in fills),D('1.5992'))
                    self.assertEqual(engine.val('cash'),D('9998.3008'))
                    self.assertEqual(engine.val('nav'),D('9998.3008'))
                    self.assertEqual(engine.val('realized'),D('-1.6992'))
                    self.assertEqual(engine.val('btc'),0)
                    variants.append(audit(ledger))
                finally: session.close()
        self.assertEqual(variants[0],variants[1])

    def test_failed_send_blocking_is_retained_without_counting_a_sent_frame(self):
        class BrokenSocket:
            def settimeout(self,_): pass
            def sendall(self,_): raise TimeoutError('synthetic blocked send')
            def close(self): pass
        with tempfile.TemporaryDirectory() as tmp, profiling(StageProfile()):
            out=Path(tmp)/'producer.json'; go=Event(); go.set(); times=[0,0]
            harness.producer(BrokenSocket(),[{'wire':b'{}','offset_ns':0}],
                             SimpleNamespace(value=0),go,Event(),Event(),times,str(out))
            receipt=load(out.read_bytes())
            self.assertEqual(receipt['sent_frames'],0)
            self.assertEqual(times[1],0)
            self.assertEqual(len(receipt['profile_send_calls']),1)
            self.assertFalse(receipt['profile_send_calls'][0]['completed'])
            self.assertGreaterEqual(receipt['profile_send_calls'][0]['ns'],0)

    def test_synthetic_profile_replays_and_preserves_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=synthetic_source(root/'source',1,3)
            before={p:p.read_bytes() for p in source.parent.rglob('*') if p.is_file()}
            receipt=run(source,root/'trial',1)
            self.assertEqual(receipt['own_raw_replay'],'PASS')
            self.assertEqual(receipt['scheduled_frames'],3)
            self.assertIn('sqlite_commit',receipt['stages'])
            self.assertEqual(before,{p:p.read_bytes() for p in before})


if __name__=='__main__': unittest.main()
