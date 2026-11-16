"""Bounded offline paired load experiment around the unchanged live application queue.

Private receipts only. The socket driver does NOT emulate native WebSocket
protocol buffering (max_queue=16); this tests the original application queue,
Capture/Session and DiagnosticBook paths. Never certifies operational readiness.
"""
import argparse
import asyncio
import base64
from collections import Counter, deque
from contextlib import ExitStack
import hashlib
import lzma
import multiprocessing as mp
import os
from pathlib import Path
import resource
import socket
import struct
import sys
import time
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from crypto_paper import live as transport
from crypto_paper.data import MAX_FRAME, NANO, dump, load, parse_time, sha
from crypto_paper.diagnostic import DiagnosticBook
from crypto_paper.engine import Ledger
from crypto_paper.runtime import Capture, Session, code_hashes, compare, digest_file, frames, manifest, verified_parts, write_json
from tools.benchmark_replay_index import audit

HEADER = struct.Struct('!IIqq')
CONFIG = dict(application_queue_frames=4096, application_queue_bytes=32*MAX_FRAME,
              max_frame_bytes=MAX_FRAME, max_queue_age_ns=500_000_000,
              configured_native_websocket_max_queue=16, native_protocol_buffer_emulated=False,
              driver_lateness_limit_ns=50_000_000, producer_start_lead_ns=500_000_000)


class TrialStopped(Exception):
    """Committed first failure ends this source schedule without resnapshot."""


def distributions(values):
    values=sorted(values)
    if not values:
        return dict(count=0,p50=None,p95=None,p99=None,max=None)
    def q(p): return values[min(len(values)-1,(len(values)*p+99)//100-1)]
    return dict(count=len(values),p50=q(50),p95=q(95),p99=q(99),max=values[-1])


def driver_fidelity(rows, tolerance=CONFIG['driver_lateness_limit_ns']):
    attempted=[r for r in rows if r['send_start_ns']]
    late=[r['send_start_ns']-r['planned_ns'] for r in attempted]
    incomplete=sum(not r.get('send_end_ns') or r['send_end_ns']<r['send_start_ns'] for r in attempted)
    return dict(send_start_lateness_ns=distributions(late),
                late_driver_frames=sum(v>tolerance for v in late),
                early_driver_frames=sum(v<0 for v in late),
                incomplete_send_frames=incomplete,
                complete_framed_prefix=bool(attempted) and not incomplete,
                tolerance_ns=tolerance,
                schedule_faithful=bool(late) and not any(v<0 or v>tolerance for v in late))


def condition_scope(status, driver, fully_sent, fully_processed, queue_failure,
                    worker_valid, cleanup_valid, producer_valid):
    """No successful-prefix timing can certify a complete-window result."""
    valid=(driver['schedule_faithful'] and driver['complete_framed_prefix'] and
           worker_valid and cleanup_valid and producer_valid)
    if valid and status=='DONE' and fully_sent and fully_processed:
        return 'FULL_WINDOW'
    if valid and status=='STOPPED_ON_FIRST_FAILURE' and queue_failure:
        return 'FIRST_QUEUE_FAILURE_PREFIX'
    return 'UNINTERPRETABLE'


def refresh_evidence(services):
    starts=[r['mono_ns'] for r in services if r['kind']=='run_begin']
    begin=starts[0] if starts else None
    clocks=[r for r in services if r['kind']=='clock' and begin is not None and r['mono_ns']-begin>=50*NANO]
    return dict(observed=bool(clocks),clock_services=clocks,
                scope='actual unchanged periodic-clock phase; no valid UTC implied')


def select_input(manifest_path, window):
    info, parts=verified_parts(manifest_path)
    if info.get('state')=='COLLECTING' or not parts:
        raise ValueError('sealed input required')
    if digest_file(manifest_path.parent/'ledger.sqlite3') != info.get('ledger_sha256'):
        raise ValueError('sealed ledger hash mismatch')
    selected=[]; start=None; epoch=None; previous=-1; observed_end=None
    interruptions=[]
    ledger=Ledger(manifest_path.parent/'ledger.sqlite3',readonly=True)
    try:
        for f in frames(manifest_path.parent,parts):
            if f['capture_id']!=info['run_id']:
                raise ValueError('source capture identity mismatch')
            expected=ledger.db.execute('SELECT digest FROM frames WHERE idx=?',(f['idx'],)).fetchone()
            if expected!=(sha(dump(f).encode()),):
                raise ValueError('source committed frame digest mismatch')
            observed_end=max(observed_end if observed_end is not None else f['mono'],f['mono'])
            if f['kind'] in ('disconnect','overflow','restart','shutdown') or (f['kind']=='connect' and start is not None):
                interruptions.append(f['mono'])
            if f['kind']!='ws': continue
            arrival=f['received_monotonic_ns']
            if start is None: start=arrival; epoch=f['connection_epoch']
            if arrival-start>=window*NANO: continue
            if arrival<previous: raise ValueError('source arrival offsets regress')
            previous=arrival
            if f['connection_epoch']!=epoch:
                raise ValueError('selected window crosses a connection epoch; no faithful resnapshot')
            wire=base64.b64decode(f['payload_bytes'],validate=True)
            if sha(wire)!=f['sha256'] or len(wire)>MAX_FRAME:
                raise ValueError('input payload hash or frame limit')
            selected.append(dict(source_idx=f['idx'],offset_ns=arrival-start,wire=wire,sha256=f['sha256']))
    finally:
        ledger.close()
    if not selected: raise ValueError('empty source schedule')
    cutoff=start+window*NANO
    if observed_end<cutoff:
        raise ValueError('insufficient committed source observation span')
    if any(start<=t<cutoff for t in interruptions):
        raise ValueError('source observation window interrupted')
    books=[load(r['wire']) for r in selected if load(r['wire']).get('channel')=='book']
    if not books or books[0].get('type')!='snapshot':
        raise ValueError('initial CRC book snapshot required')
    if not any(load(r['wire']).get('channel')=='instrument' for r in selected):
        raise ValueError('initial real instrument metadata required')
    # A quiet WS suffix is permitted only with committed observation through cutoff.
    selected[0]['source_observation']=dict(start_mono_ns=start,cutoff_mono_ns=cutoff,
        observed_end_mono_ns=observed_end,requested_seconds=window,
        uninterrupted=True,scope='committed capture horizon; not operational READY')
    identity=[dict(source_idx=r['source_idx'],offset_ns=r['offset_ns'],sha256=r['sha256']) for r in selected]
    return info,parts,selected,sha(dump(identity).encode())


def _wait_start(ready,go,stop):
    ready.set()
    while not stop.is_set():
        if go.wait(.05): return True
    return False


def wait_target(starts,stop):
    while not stop.is_set():
        left=starts.value-time.monotonic_ns()
        if left<=0: return True
        time.sleep(min(.005,left/NANO))
    return False


def producer(sock, schedule, starts, gate, ready, stop, times, receipt):
    began_cpu=time.process_time(); attempted=sent=0; error=None
    try:
        sock.settimeout(.25)
        if _wait_start(ready,gate,stop):
            for i,row in enumerate(schedule):
                target=starts.value+row['offset_ns']
                while not stop.is_set():
                    left=target-time.monotonic_ns()
                    if left<=0: break
                    time.sleep(min(.005,left/NANO))
                if stop.is_set(): break
                send=time.monotonic_ns(); times[2*i]=send; attempted+=1
                sock.sendall(HEADER.pack(len(row['wire']),i,target,send)+row['wire'])
                times[2*i+1]=time.monotonic_ns(); sent+=1
    except (OSError,TimeoutError) as exc:
        error=repr(exc)
    finally:
        sock.close()
        write_json(Path(receipt),dict(attempted_frames=attempted,sent_frames=sent,error=error,
                                     cpu_seconds=time.process_time()-began_cpu,
                                     complete_schedule=sent==len(schedule)))


def compression_worker(paths,out,starts,gate,ready,stop,receipt):
    boot=time.process_time(); began=None; work_started=None; input_bytes=output_bytes=cycles=cycle_input=0
    compressor=lzma.LZMACompressor(preset=6)
    with Path(out).open('xb') as sink:
        if _wait_start(ready,gate,stop) and wait_target(starts,stop):
            work_started=time.monotonic_ns(); began=time.process_time()
            while not stop.is_set():
                completed=True
                for path in paths:
                    with Path(path).open('rb') as source:
                        while not stop.is_set():
                            data=source.read(64*1024)
                            if not data: break
                            input_bytes+=len(data); cycle_input+=len(data)
                            packed=compressor.compress(data); sink.write(packed); output_bytes+=len(packed)
                        if stop.is_set(): completed=False; break
                if completed:
                    packed=compressor.flush(); sink.write(packed); output_bytes+=len(packed)
                    cycles+=1; cycle_input=0; compressor=lzma.LZMACompressor(preset=6)
                else: break
            packed=compressor.flush(); sink.write(packed); output_bytes+=len(packed)
    write_json(Path(receipt),dict(input_bytes=input_bytes,output_bytes=output_bytes,complete_source_cycles=cycles,
                                 partial_last_cycle=cycle_input>0,last_cycle_input_bytes=cycle_input,
                                 cpu_seconds=time.process_time()-(began or time.process_time()),
                                 initialization_cpu_seconds=(began-boot) if began else time.process_time()-boot,
                                 planned_start_mono_ns=starts.value,work_started_mono_ns=work_started,
                                 cpu_scope='after common start through cooperative flush/close; cleanup included',
                                 codec='LZMA6 on original raw segments; partial concatenated streams, not an accepted archive'))


def replay_worker(source,policy,indexed,starts,gate,ready,stop,receipt):
    boot=time.process_time(); began=None; work_started=None; count=cycles=0; current=0
    session=Session(None,'background',policy,ledger=Ledger(':memory:'))
    if indexed: session.ledger.db.execute('CREATE INDEX background_events_frame ON events(frame)')
    try:
        if _wait_start(ready,gate,stop) and wait_target(starts,stop):
            work_started=time.monotonic_ns(); began=time.process_time()
            while not stop.is_set():
                current=0
                for frame in frames(Path(source)):
                    if stop.is_set(): break
                    session.handle(frame)
                    list(session.ledger.db.execute('SELECT kind,payload FROM events WHERE frame=?',(frame['idx'],)))
                    count+=1; current+=1
                if stop.is_set(): break
                cycles+=1; current=0; session.close()
                session=Session(None,'background',policy,ledger=Ledger(':memory:'))
                if indexed: session.ledger.db.execute('CREATE INDEX background_events_frame ON events(frame)')
    finally:
        session.close()
        write_json(Path(receipt),dict(processed_frames=count,complete_source_cycles=cycles,
                                     last_cycle_frames=current,partial_last_cycle=current>0,indexed=indexed,
                                     cpu_seconds=time.process_time()-(began or time.process_time()),
                                     initialization_cpu_seconds=(began-boot) if began else time.process_time()-boot,
                                 planned_start_mono_ns=starts.value,work_started_mono_ns=work_started,
                                 cpu_scope='after common start through cooperative flush/close; cleanup included',
                                     scope='memory Session reconstruction plus original per-frame lookup; not operational acceptance'))


class DriverState:
    def __init__(self):
        self.pending=deque(); self.reads=[]; self.ws=None
        self.eof=False; self.connections=0; self.capture_services=[]; self.session_services=[]
        self.dequeued_by_wire={}; self.queue_high_frames=0; self.queue_high_bytes=0; self.frame_full_seen=False


async def exact_read(loop,sock,size):
    data=bytearray()
    while len(data)<size:
        chunk=await loop.sock_recv(sock,size-len(data))
        if not chunk: return None
        data.extend(chunk)
    return bytes(data)


class FakeWebSocket:
    def __init__(self,sock,state,max_size):
        self.sock=sock; self.state=state; self.max_size=max_size
    async def send(self,_): pass
    async def recv(self,decode=False):
        loop=asyncio.get_running_loop()
        header=await exact_read(loop,self.sock,HEADER.size)
        if header is None:
            self.state.eof=True
            await asyncio.Event().wait()  # intentional source EOF stays open to sampler finish
        length,index,planned,sent=HEADER.unpack(header)
        if length>self.max_size: raise ValueError('driver frame exceeds approved max_size')
        wire=await exact_read(loop,self.sock,length)
        if wire is None: raise OSError('partial framed source payload')
        meta=dict(schedule_index=index,planned_ns=planned,send_start_ns=sent,read_ns=time.monotonic_ns(),payload_bytes=length)
        self.state.reads.append(meta); self.state.pending.append(meta)
        return wire
    async def __aenter__(self): return self
    async def __aexit__(self,*_): return False


def fake_connect(state,sock):
    def connect(_,*args,**kwargs):
        state.connections+=1
        if state.connections>1: raise TrialStopped('source resnapshot is unavailable; no reconnect schedule restart')
        state.ws=FakeWebSocket(sock,state,kwargs['max_size'])
        return state.ws
    return connect


def measured_queue_type(state):
    original=asyncio.Queue
    class MeasuredQueue(original):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs); self.measured_bytes=0
        def full(self):
            value=super().full(); state.frame_full_seen|=value; return value
        def put_nowait(self,item):
            super().put_nowait(item)
            self.measured_bytes+=len(item[0])
            state.queue_high_frames=max(state.queue_high_frames,self.qsize())
            state.queue_high_bytes=max(state.queue_high_bytes,self.measured_bytes)
        async def get(self):
            item=await super().get()
            state.dequeued_by_wire[id(item[0])]=time.monotonic_ns()
            self.measured_bytes-=len(item[0])
            return item
    return MeasuredQueue


class MeasuredCapture(Capture):
    def __init__(self,out,run_id,state):
        super().__init__(out,run_id); self.state=state; self.clock_unverified_diagnostic=True
    def put(self,kind,wire=b'',**kw):
        began=time.monotonic_ns()
        if kind=='ws':
            if not self.state.pending: raise RuntimeError('driver/dequeue metadata mismatch')
            meta=self.state.pending.popleft().copy()
            meta['dequeue_ns']=self.state.dequeued_by_wire.pop(id(wire))
            meta['emit_start_ns']=began
            kw['harness_driver']=meta
        f=super().put(kind,wire,**kw)
        self.state.capture_services.append(dict(frame=f['idx'],kind=kind,mono_ns=f['mono'],ns=time.monotonic_ns()-began))
        return f


class MeasuredSession(Session):
    def __init__(self,out,run_id,state,slow_seconds=0):
        super().__init__(out,run_id,'observe'); self.driver=state; self.slow_seconds=slow_seconds
    def handle(self,f):
        began=time.monotonic_ns()
        super().handle(f)
        if f['kind']=='ws' and self.slow_seconds: time.sleep(self.slow_seconds)
        self.driver.session_services.append(dict(frame=f['idx'],kind=f['kind'],ns=time.monotonic_ns()-began))
        if f['kind']=='disconnect':
            raise TrialStopped('first disconnect stops source schedule: '+f.get('reason','unknown'))


def _errors(exc):
    if isinstance(exc,BaseExceptionGroup):
        return [s for e in exc.exceptions for s in _errors(e)]
    return [f'{type(exc).__name__}: {exc}']


def _offline(*_): raise OSError('offline experiment: REST/NTP unavailable; no substitute clock')


def _cleanup(process,timeout=3):
    process.join(timeout)
    forced=process.is_alive()
    if forced: process.terminate(); process.join(2)
    return dict(exitcode=process.exitcode,forced_termination=forced,alive=process.is_alive())


def trial(manifest_path,out,window,loaded,indexed=False,prepared=None,slow_seconds=0):
    if not 1<=window<=60: raise ValueError('trial schedule window must be1..60seconds')
    out=Path(out); out.mkdir(parents=True,exist_ok=False)
    trial_start_utc=time.time_ns()
    info,parts,schedule,input_hash=prepared or select_input(Path(manifest_path),window)
    build=code_hashes(); source_hash=digest_file(Path(manifest_path)); source_ledger_hash=digest_file(Path(manifest_path).parent/'ledger.sqlite3')
    harness_hash=digest_file(Path(__file__))
    if build!=info['code_hashes'] or load(Path(manifest_path).read_bytes())!=info:
        raise ValueError('prepared source build or manifest changed between arms')
    raw_before={str(p):digest_file(p) for p in parts}
    if any(raw_before[str(p)]!=info['parts'][str(p.relative_to(Path(manifest_path).parent))] for p in parts):
        raise ValueError('prepared source raw parts changed')
    context=mp.get_context('fork'); go=context.Event(); stop=context.Event(); ready=context.Event()
    start=context.Value('q',0); send_times=context.RawArray('q',len(schedule)*2)
    parent_sock,child_sock=socket.socketpair(); parent_sock.setblocking(False)
    buffer_sizes=dict(send=child_sock.getsockopt(socket.SOL_SOCKET,socket.SO_SNDBUF),receive=parent_sock.getsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF))
    producer_process=context.Process(target=producer,args=(child_sock,schedule,start,go,ready,stop,send_times,str(out/'producer.json')))
    workers=[]; worker_readies=[]
    state=DriverState(); session=MeasuredSession(out,'offline-paired-trial',state,slow_seconds); capture=MeasuredCapture(out,'offline-paired-trial',state)
    processes=[]; status='NOT_STARTED'; failure=[]; timed_ns=0
    try:
        producer_process.start(); processes.append(producer_process); child_sock.close()
        if loaded:
            for name,target,args in [
                ('compression',compression_worker,([str(p) for p in parts],str(out/'compression.partial.xz'),start,go)),
                ('replay',replay_worker,(str(Path(manifest_path).parent),info['policy'],indexed,start,go))]:
                r=context.Event(); worker_readies.append(r)
                p=context.Process(target=target,args=(*args,r,stop,str(out/f'{name}.json')))
                p.start(); processes.append(p); workers.append((name,p))
        for r in [ready,*worker_readies]:
            if not r.wait(5): raise RuntimeError('worker readiness timeout before common start')
        start.value=time.monotonic_ns()+CONFIG['producer_start_lead_ns']
        go.set(); began=time.monotonic_ns()
        async def execute():
            async with asyncio.timeout(window+10):
                return await transport.live(session,capture,window+1,None)
        with ExitStack() as stack:
            queue_type=measured_queue_type(state)
            stack.enter_context(patch.object(transport.asyncio,'Queue',queue_type))
            stack.enter_context(patch('websockets.asyncio.client.connect',fake_connect(state,parent_sock)))
            stack.enter_context(patch.object(transport,'public',_offline))
            stack.enter_context(patch.object(transport,'ntp',_offline))
            try:
                status=asyncio.run(execute())[0]
            except Exception as exc:
                failure=_errors(exc); status='STOPPED_ON_FIRST_FAILURE' if failure and all(s.startswith('TrialStopped:') for s in failure) else 'ERROR'
        timed_ns=time.monotonic_ns()-began
    finally:
        stop.set(); go.set()
        cleanup=[_cleanup(p) for p in processes]
        parent_sock.close()
        try: child_sock.close()
        except OSError: pass
        session.handle(capture.put('shutdown',reason=status,epoch=session.book.epoch))
        capture.close(); coverage=session.metrics(); session.close()
    if any(c['alive'] for c in cleanup):
        write_json(out/'cleanup-failed.json',dict(processes=cleanup,condition_interpretable=False))
        raise RuntimeError('trial child remains alive; abort paired series')
    manifest(out,'offline-paired-trial','observe',trial_start_utc,state='DIAGNOSTIC',offline_queue_experiment=True)
    audits=[]; raw=[]; diagnostic=DiagnosticBook()
    rebuilt=Session(None,'offline-paired-trial','observe',ledger=Ledger(':memory:'))
    source=Ledger(out/'ledger.sqlite3',readonly=True)
    try:
        for f in frames(out):
            rebuilt.handle(f); diagnostic.handle(f)
            if f['kind']=='ws': raw.append(f)
        if not compare(source,rebuilt.ledger)['equal'] or source.state!=rebuilt.ledger.state:
            raise ValueError('trial own-raw ordered/account replay mismatch')
        audits=[audit(source),audit(rebuilt.ledger)]
        if audits[0]!=audits[1] or not audits[0]['reconciled']: raise ValueError('trial audit mismatch')
    finally: source.close(); rebuilt.close()
    if code_hashes()!=build or digest_file(Path(__file__))!=harness_hash or digest_file(Path(manifest_path))!=source_hash or digest_file(Path(manifest_path).parent/'ledger.sqlite3')!=source_ledger_hash or raw_before!={str(p):digest_file(p) for p in parts}:
        raise ValueError('source build or sealed input changed')
    indices=[f['harness_driver']['schedule_index'] for f in raw]
    if indices!=list(range(len(raw))) or any(f['sha256']!=schedule[i]['sha256'] for i,f in enumerate(raw)):
        raise ValueError('processed schedule is not the identical planned prefix')
    actual_clock=bool(session.clock)
    if actual_clock or coverage['ready_seconds'] or audits[0]['event_counts'].get('fill',0):
        raise ValueError('invalid-clock experiment unexpectedly granted readiness or fills')
    dequeued={f['harness_driver']['schedule_index']:f for f in raw}
    reads={r['schedule_index']:r for r in state.reads}
    rows=[]
    for i,row in enumerate(schedule):
        timing=dict(schedule_index=i,source_idx=row['source_idx'],offset_ns=row['offset_ns'],planned_ns=start.value+row['offset_ns'],
                    send_start_ns=send_times[2*i],send_end_ns=send_times[2*i+1],read_ns=reads.get(i,{}).get('read_ns'),
                    dequeue_ns=dequeued[i]['harness_driver']['dequeue_ns'] if i in dequeued else None,
                    queue_received_mono=dequeued[i].get('queue_received_mono') if i in dequeued else None)
        rows.append(timing)
    failures=[f for f in frames(out) if f['kind'] in ('disconnect','overflow')]
    worker_results={name:(load((out/f'{name}.json').read_bytes()) if (out/f'{name}.json').exists() else {'receipt_missing':True}) for name,_ in workers}
    driver=driver_fidelity(rows)
    driver['fidelity_scope']='attempted prefix only; unsent remainder was not offered after first failure'
    producer_result=load((out/'producer.json').read_bytes()) if (out/'producer.json').exists() else {'receipt_missing':True}
    worker_valid=(not loaded or (worker_results.get('compression',{}).get('input_bytes',0)>0 and worker_results.get('replay',{}).get('processed_frames',0)>0))
    cleanup_valid=all(not c['forced_termination'] and not c['alive'] and c['exitcode']==0 for c in cleanup)
    queue_reasons=[f.get('reason') for f in failures if f['kind']=='disconnect']
    fully_sent=sum(bool(r['send_end_ns']) for r in rows)==len(schedule)
    fully_processed=len(raw)==len(schedule)
    scope=condition_scope(status,driver,fully_sent,fully_processed,
        any(reason in ('WS queue overflow','WS queue too old') for reason in queue_reasons),
        worker_valid,cleanup_valid,not producer_result.get('receipt_missing') and producer_result.get('error') is None)
    refresh=refresh_evidence(state.capture_services)
    refresh['required_for_full_window']=window>=50
    if scope=='FULL_WINDOW' and window>=50 and not refresh['observed']:
        scope='UNINTERPRETABLE'
    interpretable=scope!='UNINTERPRETABLE'
    result=dict(schema_version='offline-paired-queue-v1',mode='loaded' if loaded else 'idle',indexed_background=indexed,
        status=status,errors=failure,window_seconds=window,live_sample_window_seconds=window+1,timed_wall_ns=timed_ns,
        slow_session_test_injection_seconds=slow_seconds,
        config=CONFIG,socket_buffers=buffer_sizes,start_mono_ns=start.value,input_schedule_sha256=input_hash,
        application_queue_high_water_frames=state.queue_high_frames,application_queue_high_water_bytes=state.queue_high_bytes,
        source_manifest_sha256=source_hash,source_part_hashes=info['parts'],all_workers_ready_before_start=True,package_hashes=build,harness_sha256=digest_file(Path(__file__)),
        scheduled_frames=len(schedule),attempted_frames=sum(bool(r['send_start_ns']) for r in rows),sent_frames=sum(bool(r['send_end_ns']) for r in rows),
        socket_read_frames=len(reads),processed_frames=len(raw),unprocessed_scheduled_frames=len(schedule)-len(raw),
        read_but_not_processed_frames=len(reads)-len(raw),intentional_source_eof=state.eof,connections=state.connections,
        driver=driver,timing_rows=rows,
        background_work_observed=worker_valid,condition_interpretable=interpretable,
        condition_scope=scope,full_window_valid=scope=='FULL_WINDOW',
        matched_prefix_required=scope=='FIRST_QUEUE_FAILURE_PREFIX',
        source_observation=schedule[0]['source_observation'],refresh_phase=refresh,
        load_representativeness='UNVERIFIED: activity is not sustained overlap acceptance',
        cross_arm_financial_equivalence='NOT_EVALUATED',producer=producer_result,
        scheduled_input_fully_sent=sum(bool(r['send_end_ns']) for r in rows)==len(schedule),
        scheduled_input_fully_processed=len(raw)==len(schedule),actual_processed_input_prefix_verified=True,
        threshold_failures=dict(frame_cap=int('WS queue overflow' in queue_reasons and state.frame_full_seen),
                                byte_cap=int('WS queue overflow' in queue_reasons and not state.frame_full_seen),
                                age_cap=int('WS queue too old' in queue_reasons)),
        send_end_lateness_ns=distributions([r['send_end_ns']-r['planned_ns'] for r in rows if r['send_end_ns']]),
        send_duration_ns=distributions([r['send_end_ns']-r['send_start_ns'] for r in rows if r['send_end_ns']]),
        read_lateness_ns=distributions([r['read_ns']-r['planned_ns'] for r in rows if r['read_ns']]),
        dequeue_lateness_ns=distributions([r['dequeue_ns']-r['planned_ns'] for r in rows if r['dequeue_ns']]),
        app_queue_age_ns=distributions([r['dequeue_ns']-r['queue_received_mono'] for r in rows if r['dequeue_ns']]),
        capture_service_ns=distributions([r['ns'] for r in state.capture_services if r['kind']=='ws']),
        session_service_ns=distributions([r['ns'] for r in state.session_services if r['kind']=='ws']),
        stage_services=dict(capture=state.capture_services,session=state.session_services),failure_frames=failures,
        coverage=coverage,diagnostic=diagnostic.metrics(),background=worker_results,process_cleanup=cleanup,
        own_raw_ordered_events_and_account_replay='PASS',own_ledger_audit=audits[0],clock_valid=actual_clock,source_raw_parts_unchanged=True,
        real_source_financial_validation='observation-only original input; zero real fills expected',operational_acceptance=False,
        limitations=['native WebSocket framing/max_queue16 not emulated; original application queue only',
                     'socket pre-read lateness can be invisible to the application500ms gate; driver/read/dequeue timing retained',
                     'unchanged original payload exchange timestamps; UTC remains unverified and production READY false',
                     'representative workers are bounded partial work, not accepted archive or full report',
                     'capture/session instrumentation adds equal work in both arms'])
    write_json(out/'receipt.json',result)
    return result


def experiment(manifest_path,out,window=20,indexed=False,repeats=2):
    if repeats not in (1,2): raise ValueError('one AB or two ABBA pairs only')
    if not 1<=window<=60: raise ValueError('trial schedule window must be1..60seconds')
    prepared=select_input(Path(manifest_path),window)
    out=Path(out); out.mkdir(parents=True,exist_ok=False)
    results=[]
    order=[False,True] if repeats==1 else [False,True,True,False]
    for number,loaded in enumerate(order,1):
        r=trial(Path(manifest_path),out/f"{number:02d}-{'loaded' if loaded else 'idle'}",window,loaded,indexed,prepared)
        results.append({k:v for k,v in r.items() if k not in ('timing_rows','stage_services','failure_frames')})
        if not r['condition_interpretable']: break
    receipt=dict(schema_version='offline-queue-paired-series-v1',planned_order=['loaded' if v else 'idle' for v in order],actual_order=[r['mode'] for r in results],trials=results,
        stopped_on_uninterpretable_condition=len(results)<len(order),
        input_schedule_sha256=prepared[3],harness_sha256=digest_file(Path(__file__)),operational_acceptance=False,
        full_window_series_valid=bool(results) and len(results)==len(order) and all(r['full_window_valid'] for r in results),
        cross_arm_financial_equivalence='NOT_EVALUATED',
        interpretation='same schedule; full windows and first-failure prefixes are distinct; load overlap and common-prefix accounting require independent review')
    write_json(out/'series.json',receipt)
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True); p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seconds',type=int,default=20); p.add_argument('--pairs',type=int,choices=(1,2),default=2)
    p.add_argument('--indexed-background',action='store_true')
    a=p.parse_args(); experiment(a.manifest,a.out,a.seconds,a.indexed_background,a.pairs)


if __name__=='__main__': main()
