"""Private stage profiling around the offline harness, with durability unchanged.

Use a retained sealed manifest to profile recorded input. --synthetic generates
repeatable test traffic; its results cannot identify a historical bottleneck.
Raw inputs, output captures and detailed profile receipts must remain private.
"""
import argparse
from contextlib import contextmanager
from pathlib import Path
import time
import sqlite3
from unittest.mock import patch

from crypto_paper.data import NANO, dump, load
from crypto_paper.runtime import Capture, Session, manifest, write_json, digest_file
from crypto_paper.verify import META, UTC, market
from tools import replay_queue_load as harness


class StageProfile:
    def __init__(self):
        self.rows=[]
        self.active=False
        self.session_active=False

    def measure(self, stage, call, *args, **kwargs):
        began=time.perf_counter_ns(); cpu=time.process_time_ns()
        try:
            return call(*args,**kwargs)
        finally:
            self.rows.append(dict(stage=stage,ns=time.perf_counter_ns()-began,cpu_ns=time.process_time_ns()-cpu))

    def summary(self):
        return {stage:dict(harness.distributions([r['ns'] for r in self.rows if r['stage']==stage]),
                           total_ns=sum(r['ns'] for r in self.rows if r['stage']==stage),
                           total_cpu_ns=sum(r['cpu_ns'] for r in self.rows if r['stage']==stage))
                for stage in sorted({r['stage'] for r in self.rows})}


class TimedStream:
    def __init__(self, stream, profile):
        self.stream,self.profile=stream,profile

    def write(self, data):
        return self.profile.measure('capture_write',self.stream.write,data)

    def flush(self):
        return self.profile.measure('capture_flush',self.stream.flush)

    def __getattr__(self,name):
        return getattr(self.stream,name)


@contextmanager
def profiling(profile, exclusive=False):
    """Single-process foreground hooks; every real write/fsync/commit still runs."""
    original_producer=harness.producer
    original_connect=sqlite3.connect
    original_open=Path.open
    original_sync=harness.os.fsync
    original_capture=harness.MeasuredCapture
    original_session=harness.MeasuredSession

    def opened(path,*args,**kwargs):
        stream=original_open(path,*args,**kwargs)
        mode=args[0] if args else kwargs.get('mode','r')
        return TimedStream(stream,profile) if profile.active and mode=='xb' else stream

    def synced(fd):
        if profile.active:
            return profile.measure('capture_fsync',original_sync,fd)
        return original_sync(fd)

    class ProfiledCapture(original_capture):
        def put(self,*args,**kwargs):
            profile.active=True
            try:
                return profile.measure('capture_total',super().put,*args,**kwargs)
            finally:
                profile.active=False

    def profiled_producer(sock,schedule,starts,gate,ready,stop,times,receipt):
        calls=[]
        class TimedSocket:
            def sendall(self,data):
                began=time.monotonic_ns(); completed=False
                try:
                    result=sock.sendall(data); completed=True
                    return result
                finally:
                    calls.append(dict(schedule_index=len(calls),ns=time.monotonic_ns()-began,
                                      completed=completed))
            def __getattr__(self,name): return getattr(sock,name)
        original_producer(TimedSocket(),schedule,starts,gate,ready,stop,times,receipt)
        result=load(Path(receipt).read_bytes())
        result['profile_send_calls']=calls
        write_json(Path(receipt),result)

    class ProfileConnection(sqlite3.Connection):
        def commit(self):
            if profile.session_active:
                return profile.measure('sqlite_commit',super().commit)
            return super().commit()

    def connect(*args,**kwargs):
        kwargs['factory']=ProfileConnection
        return original_connect(*args,**kwargs)

    class ProfiledSession(original_session):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            if exclusive:
                self.ledger.db.execute('PRAGMA locking_mode=EXCLUSIVE')
            if self.ledger.db.execute('PRAGMA synchronous').fetchone()!=(2,):
                raise ValueError('FULL durability required')
            if self.ledger.db.execute('PRAGMA journal_mode').fetchone()!=('persist',):
                raise ValueError('PERSIST journal required')

        def handle(self,frame):
            profile.session_active=True
            try:
                return profile.measure('session_total',super().handle,frame)
            finally:
                profile.session_active=False

    with patch.object(harness,'producer',profiled_producer), patch.object(sqlite3,'connect',connect), patch.object(Path,'open',opened), patch.object(harness.os,'fsync',synced), \
         patch.object(harness,'MeasuredCapture',ProfiledCapture), \
         patch.object(harness,'MeasuredSession',ProfiledSession):
        yield


def synthetic_source(out, seconds, rate):
    """Uniform synthetic book traffic with a proved sealed observation horizon."""
    out=Path(out); out.mkdir(parents=True,exist_ok=False)
    session=Session(out,'synthetic-profile','observe')
    capture=Capture(out,'synthetic-profile')
    count=max(2,int(seconds*rate))
    try:
        for index in range(count):
            offset=index*seconds*NANO//count
            if index==0:
                session.handle(capture.put('connect',epoch=1,utc=UTC,mono=0))
                wire={'channel':'instrument','data':{'pairs':[META|{'symbol':'BTC/USD'}]}}
            else:
                wire=market(utc=UTC+offset)
                if index>1: wire['type']='update'
            frame=capture.put('ws',dump(wire).encode(),epoch=1,utc=UTC+offset,mono=offset)
            session.handle(frame)
        session.handle(capture.put('shutdown',epoch=1,utc=UTC+seconds*NANO,mono=seconds*NANO))
    finally:
        capture.close(); session.close()
    manifest(out,'synthetic-profile','observe',UTC,state='DIAGNOSTIC',synthetic=True)
    return out/'manifest.json'


def run(manifest_path,out,seconds,loaded=False,exclusive=False):
    profile=StageProfile()
    with profiling(profile,exclusive):
        receipt=harness.trial(Path(manifest_path),Path(out),seconds,loaded)
    stages=profile.summary()
    total=stages.get('capture_total',{}).get('total_ns',0)
    children=sum(stages.get(k,{}).get('total_ns',0) for k in ('capture_write','capture_flush','capture_fsync'))
    result=dict(schema_version='queue-delivery-profile-v1',profiler_sha256=digest_file(Path(__file__)),
                source_manifest_sha256=receipt['source_manifest_sha256'],
                exclusive_foreground_ledger=exclusive,stages=stages,
                capture_nonwrite_residual_ns=total-children,
                send_blocking_ns=harness.distributions([r['ns'] for r in receipt['producer'].get('profile_send_calls',[])]),
                failed_send_blocking_ns=harness.distributions([r['ns'] for r in receipt['producer'].get('profile_send_calls',[]) if not r['completed']]),
                send_start_lateness_ns=receipt['driver']['send_start_lateness_ns'],
                send_end_lateness_ns=receipt['send_end_lateness_ns'],
                read_lateness_ns=receipt['read_lateness_ns'],
                dequeue_lateness_ns=receipt['dequeue_lateness_ns'],
                processed_frames=receipt['processed_frames'],scheduled_frames=receipt['scheduled_frames'],
                status=receipt['status'],condition_scope=receipt['condition_scope'],
                own_raw_replay=receipt['own_raw_ordered_events_and_account_replay'],
                caveats=['foreground wall times include scheduler pauses; nested Capture stages are not additive to total',
                         'SQLite FULL commit time is included in Session, not capture fsync',
                         'instrumentation overhead affects all measured conditions; raw receipts private'])
    write_json(Path(out)/'profile.json',result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--manifest',type=Path)
    source.add_argument('--synthetic',action='store_true')
    parser.add_argument('--seconds',type=int,default=10)
    parser.add_argument('--rate',type=int,default=168)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--loaded',action='store_true')
    parser.add_argument('--exclusive-ledger',action='store_true',help='experimental foreground single-writer lock only; blocks concurrent readers')
    args=parser.parse_args()
    if not 1<=args.seconds<=60 or not 1<=args.rate<=1000:
        parser.error('bounded seconds 1..60 and synthetic rate 1..1000 required')
    args.out.mkdir(parents=True,exist_ok=False)
    path=args.manifest or synthetic_source(args.out/'source',args.seconds,args.rate)
    result=run(path,args.out/'trial',args.seconds,args.loaded,args.exclusive_ledger)
    print(dump(result))


if __name__=='__main__': main()
