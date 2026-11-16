"""Synthetic source-queue gates and driver lifecycle; no real-data experiment."""
import asyncio
from pathlib import Path
import tempfile
import time
import unittest
from threading import Event
from types import SimpleNamespace
from unittest.mock import patch

from crypto_paper import live as transport
from crypto_paper.data import NANO, MAX_FRAME, dump, load
from crypto_paper.runtime import Capture, Session, manifest
from crypto_paper.verify import UTC, META, market
from tools.replay_queue_load import CONFIG, DriverState, MeasuredCapture, MeasuredSession, TrialStopped, driver_fidelity, trial, select_input, _errors, condition_scope, producer, refresh_evidence


class ReplayQueueTests(unittest.TestCase):
    def source(self,root, interrupted=False):
        out=root/'source'; out.mkdir(); cap=Capture(out,'synthetic'); s=Session(out,'synthetic','observe')
        try:
            s.handle(cap.put('connect',epoch=1,utc=UTC,mono=0))
            s.handle(cap.put('ws',dump({'channel':'instrument','data':{'pairs':[META|{'symbol':'BTC/USD'}]}}).encode(),epoch=1,utc=UTC,mono=0))
            s.handle(cap.put('ws',dump(market()).encode(),epoch=1,utc=UTC+NANO//100,mono=NANO//100))
            if interrupted:
                s.handle(cap.put('disconnect',epoch=1,utc=UTC+NANO//2,mono=NANO//2,reason='synthetic interruption'))
            s.handle(cap.put('shutdown',epoch=1,utc=UTC+2*NANO,mono=2*NANO))
        finally: cap.close(); s.close()
        manifest(out,'synthetic','observe',UTC,state='DIAGNOSTIC')
        return out/'manifest.json'

    def test_driver_lateness_cannot_hide_behind_fresh_app_queue(self):
        rows=[dict(planned_ns=100,send_start_ns=100+CONFIG['driver_lateness_limit_ns']+1)]
        self.assertFalse(driver_fidelity(rows)['schedule_faithful'])
        self.assertEqual(driver_fidelity(rows)['late_driver_frames'],1)

    def test_source_span_is_proved_before_trial_or_children_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=self.source(root)
            with patch('tools.replay_queue_load.mp.get_context') as processes:
                with self.assertRaisesRegex(ValueError,'source observation span'):
                    trial(source,root/'rejected',60,False)
                processes.assert_not_called()
            prepared=select_input(source,1)
            self.assertTrue(prepared[2][0]['source_observation']['uninterrupted'])
            self.assertGreaterEqual(prepared[2][0]['source_observation']['observed_end_mono_ns'],NANO)

    def test_interrupted_source_is_not_a_quiet_observation_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=self.source(Path(tmp),interrupted=True)
            with self.assertRaisesRegex(ValueError,'source observation window interrupted'):
                select_input(source,1)

    def test_driver_rejects_early_send_and_incomplete_framing(self):
        early=driver_fidelity([dict(planned_ns=100,send_start_ns=99,send_end_ns=101)])
        self.assertFalse(early['schedule_faithful'])
        self.assertEqual(early['early_driver_frames'],1)
        partial=driver_fidelity([dict(planned_ns=100,send_start_ns=100,send_end_ns=0)])
        self.assertFalse(partial['complete_framed_prefix'])
        self.assertEqual(partial['incomplete_send_frames'],1)

    def test_scope_distinguishes_full_window_failure_prefix_and_errors(self):
        driver=driver_fidelity([dict(planned_ns=100,send_start_ns=100,send_end_ns=101),
                                dict(planned_ns=200,send_start_ns=0,send_end_ns=0)])
        self.assertTrue(driver['schedule_faithful'])  # attempted prefix only
        self.assertEqual(condition_scope('DONE',driver,False,False,False,True,True,True),'UNINTERPRETABLE')
        self.assertEqual(condition_scope('DONE',driver,True,True,False,True,True,True),'FULL_WINDOW')
        self.assertEqual(condition_scope('STOPPED_ON_FIRST_FAILURE',driver,False,False,True,True,True,True),'FIRST_QUEUE_FAILURE_PREFIX')
        self.assertEqual(condition_scope('ERROR',driver,True,True,False,True,True,True),'UNINTERPRETABLE')
        self.assertEqual(condition_scope('DONE',driver,True,True,False,True,True,False),'UNINTERPRETABLE')

    def test_partial_send_error_never_completes_a_frame(self):
        class PartialSocket:
            closed=False
            def settimeout(self,_): pass
            def sendall(self,_): raise OSError('synthetic partial frame')
            def close(self): self.closed=True
        with tempfile.TemporaryDirectory() as tmp:
            sock=PartialSocket(); go=Event(); go.set(); times=[0,0]
            receipt=Path(tmp)/'producer.json'
            producer(sock,[{'wire':b'{}','offset_ns':0}],SimpleNamespace(value=0),
                     go,Event(),Event(),times,str(receipt))
            result=load(receipt.read_bytes())
            self.assertEqual(result['attempted_frames'],1)
            self.assertEqual(result['sent_frames'],0)
            self.assertFalse(result['complete_schedule'])
            self.assertIn('partial frame',result['error'])
            self.assertEqual(times[1],0); self.assertTrue(sock.closed)

    def test_refresh_phase_requires_actual_late_clock_service(self):
        start={'kind':'run_begin','mono_ns':NANO,'ns':1}
        early={'kind':'clock','mono_ns':50*NANO,'ns':1}
        actual={'kind':'clock','mono_ns':51*NANO,'ns':1}
        self.assertFalse(refresh_evidence([start,early])['observed'])
        self.assertEqual(refresh_evidence([start,actual])['clock_services'],[actual])

    def test_real_driver_intentional_eof_no_reconnect_and_own_raw_replays(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=self.source(root)
            import websockets.asyncio.client as client
            original_connect=client.connect; original_public=transport.public
            r=trial(source,root/'trial',1,False)
            self.assertIs(client.connect,original_connect); self.assertIs(transport.public,original_public)
            self.assertEqual(r['status'],'DONE')
            self.assertTrue(r['intentional_source_eof'])
            self.assertEqual(r['connections'],1)
            self.assertEqual(r['sent_frames'],2)
            self.assertEqual(r['processed_frames'],2)
            self.assertEqual(r['own_raw_ordered_events_and_account_replay'],'PASS')
            self.assertEqual(r['own_ledger_audit']['event_counts'].get('fill',0),0)
            self.assertFalse(r['clock_valid'])
            self.assertTrue(all(not p['alive'] for p in r['process_cleanup']))

    def test_original_frame_queue_gate_and_first_failure_restore_factories(self):
        class FullQueue(asyncio.Queue):
            def full(self): return True
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=self.source(root)
            import websockets.asyncio.client as client
            old_connect=client.connect; old_public=transport.public
            with patch.object(transport.asyncio,'Queue',FullQueue):
                r=trial(source,root/'failed',1,False)
            self.assertIs(client.connect,old_connect); self.assertIs(transport.public,old_public)
            self.assertEqual(r['config']['application_queue_frames'],4096)
            self.assertEqual(r['status'],'STOPPED_ON_FIRST_FAILURE')
            self.assertEqual(r['connections'],1)
            self.assertGreater(r['unprocessed_scheduled_frames'],0)
            self.assertTrue(any(f.get('reason')=='WS queue overflow' for f in r['failure_frames']))

    def test_original_byte_queue_gate_uses_32MiB_without_processing_fake_payloads(self):
        class NeverDrain(asyncio.Queue):
            async def get(self): await asyncio.Event().wait()
        class FloodWS:
            def __init__(self): self.count=0
            async def __aenter__(self): return self
            async def __aexit__(self,*_): return False
            async def send(self,_): pass
            async def recv(self,**_):
                self.count+=1
                if self.count<=33: return b'{}'+b' '*(MAX_FRAME-2)
                await asyncio.Event().wait()
        with tempfile.TemporaryDirectory() as tmp:
            state=DriverState(); out=Path(tmp); cap=MeasuredCapture(out,'gate',state); s=MeasuredSession(out,'gate',state)
            try:
                with patch.object(transport.asyncio,'Queue',NeverDrain), \
                     patch('websockets.asyncio.client.connect',lambda *a,**k:FloodWS()), \
                     patch.object(transport,'public',side_effect=OSError('offline')):
                    with self.assertRaises(ExceptionGroup) as caught:
                        asyncio.run(transport.live(s,cap,1,None))
                self.assertTrue(any('first disconnect' in e for e in _errors(caught.exception)))
                self.assertEqual(CONFIG['application_queue_bytes'],32*MAX_FRAME)
                self.assertEqual(s.ledger.db.execute("SELECT count(*) FROM frames").fetchone()[0]>0,True)
            finally: cap.close(); s.close()

    def test_original_age_gate_stops_before_processing_old_queued_frame(self):
        class OldQueue(asyncio.Queue):
            async def get(self):
                return b'{}',time.monotonic_ns()-CONFIG['max_queue_age_ns']-1,time.time_ns()
        class QuietWS:
            async def __aenter__(self): return self
            async def __aexit__(self,*_): return False
            async def send(self,_): pass
            async def recv(self,**_): await asyncio.Event().wait()
        with tempfile.TemporaryDirectory() as tmp:
            state=DriverState(); out=Path(tmp); cap=MeasuredCapture(out,'age',state); s=MeasuredSession(out,'age',state)
            try:
                with patch.object(transport.asyncio,'Queue',OldQueue), \
                     patch('websockets.asyncio.client.connect',lambda *a,**k:QuietWS()), \
                     patch.object(transport,'public',side_effect=OSError('offline')):
                    with self.assertRaises(ExceptionGroup) as caught:
                        asyncio.run(transport.live(s,cap,1,None))
                self.assertTrue(any('WS queue too old' in e for e in _errors(caught.exception)))
                self.assertEqual(len([r for r in state.session_services if r['kind']=='ws']),0)
            finally: cap.close(); s.close()

    def test_representative_load_workers_are_ready_bounded_and_stopped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=self.source(root)
            r=trial(source,root/'loaded',1,True)
            self.assertTrue(r['all_workers_ready_before_start'])
            self.assertTrue(r['background_work_observed'])
            self.assertGreater(r['background']['compression']['input_bytes'],0)
            self.assertGreater(r['background']['replay']['processed_frames'],0)
            self.assertTrue(all(not p['alive'] for p in r['process_cleanup']))

    def test_resealed_raw_change_does_not_match_committed_source_frame(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=self.source(Path(tmp)); part=p.parent/'raw/000001.jsonl'
            rows=part.read_bytes().splitlines(); f=load(rows[1]); f['channel']='changed'
            rows[1]=dump(f).encode(); part.write_bytes(b'\n'.join(rows)+b'\n')
            manifest(p.parent,'synthetic','observe',UTC,state='DIAGNOSTIC')
            with self.assertRaisesRegex(ValueError,'committed frame digest'):
                select_input(p,1)

    def test_prepared_build_mismatch_is_rejected_before_process_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); p=self.source(root); prepared=select_input(p,1)
            prepared[0]['code_hashes']['engine.py']='bad'
            with self.assertRaisesRegex(ValueError,'between arms'):
                trial(p,root/'rejected',1,False,prepared=prepared)


if __name__=='__main__': unittest.main()
