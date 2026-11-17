"""Fixed-slot scratch sandbox for the descriptive two-arm queue diagnostic.

Linux x86-64 + bubblewrap + KEEP_SIZE preallocation required; fail closed.
The entire evidence root is charged, but only fresh, preallocated output files
are writable. No input/evidence deletion and no private dispatch by default.
"""
import argparse
from contextlib import contextmanager
import ctypes
from dataclasses import dataclass
import fcntl
import json
import os
from pathlib import Path
import platform
import resource
import shutil
import signal
import stat
import struct
import subprocess
import sys
from unittest.mock import patch

from crypto_paper.data import dump, load
from crypto_paper.engine import Ledger
from tools import replay_queue_load as harness

MIB=1024**2
G=5*1024*MIB
F=2*1024*MIB
IPC=8*MIB


@dataclass(frozen=True)
class Budget:
    file_limit: int=64*MIB
    reserve: int=256*MIB
    cap: int=G
    floor: int=F

    @property
    def allowance(self): return 56*self.file_limit

    def validate(self):
        if not 0<self.file_limit<=64*MIB or not IPC<=self.reserve<=256*MIB:
            raise ValueError('invalid file/stop bound')
        if not 0<self.cap<=G or self.floor<F:
            raise ValueError('global cap/floor cannot be relaxed')


def charge(root):
    """Conservative per-path charge, including directories and retained inputs."""
    total=0
    for path in [root,*root.rglob('*')]:
        value=path.lstat()
        if not (stat.S_ISREG(value.st_mode) or stat.S_ISDIR(value.st_mode)):
            raise ValueError('non-regular entry in evidence root')
        total+=max(value.st_size,value.st_blocks*512)
    return total


def slots(out):
    paths=[]
    for arm in ('01-idle','02-loaded'):
        base=out/arm
        paths.extend(base/name for name in ('raw/000001.jsonl','ledger.sqlite3',
                                           'ledger.sqlite3-journal','bars.jsonl','compression.partial.xz'))
        for name in ('producer','compression','replay','cleanup-failed','manifest','receipt'):
            paths.extend((base/f'{name}.json',base/f'{name}.tmp'))
        paths.extend(base/f'reserved-{i}' for i in range(3))
    paths.extend(out/name for name in ('series.json','series.tmp','plan.json','guard.json',
                                      'guard.tmp','stdout.log','stderr.log','reserved-common'))
    paths.extend(out/'temporary'/f'slot-{i}' for i in range(8))
    assert len(paths)==len(set(paths))==56
    return paths


def preallocate(path,limit):
    """Allocate the complete writable range while preserving logical contents."""
    fd=os.open(path,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        lib=ctypes.CDLL(None,use_errno=True)
        if lib.fallocate(fd,1,ctypes.c_longlong(0),ctypes.c_longlong(limit)):
            raise OSError(ctypes.get_errno(),'KEEP_SIZE preallocation unavailable')
        os.fsync(fd)
        value=os.fstat(fd)
        if value.st_size>limit or value.st_blocks*512!=limit:
            raise ValueError('filesystem did not provide exact reserved extent charge')
    finally: os.close(fd)


def prepare(root,manifest,out,budget=Budget(),seconds=60):
    budget.validate()
    if not 1<=seconds<=60: raise ValueError('bounded window required')
    root,manifest,out=map(lambda p:Path(p).resolve(),(root,manifest,out))
    if not out.is_relative_to(root) or not manifest.is_relative_to(root):
        raise ValueError('input and outputs must be inside counted root')
    if out.exists() or out.is_relative_to(manifest.parent) or manifest.parent.is_relative_to(out):
        raise ValueError('fresh output separate from retained input required')
    current=charge(root); reservation=budget.allowance+budget.reserve
    if current+reservation>budget.cap or shutil.disk_usage(root).free<budget.floor+reservation:
        raise ValueError('global reservation or free-space admission failed')
    destinations=slots(out)
    for path in destinations: path.parent.mkdir(parents=True,exist_ok=True)
    # Empty standard ledgers avoid bootstrap truncation inside the restricted run.
    for arm in ('01-idle','02-loaded'):
        ledger=Ledger(out/arm/'ledger.sqlite3'); ledger.close()
    for path in destinations: preallocate(path,budget.file_limit)
    if charge(root)+budget.reserve>budget.cap or shutil.disk_usage(root).free<budget.floor+budget.reserve:
        raise ValueError('post-allocation global admission failed; preserve preparation')
    plan=dict(root=str(root),manifest=str(manifest),out=str(out),seconds=seconds,budget=budget.__dict__,
              files=[str(p) for p in destinations],input_manifest_sha256=harness.digest_file(manifest),
              harness_sha256=harness.digest_file(Path(harness.__file__)),
              launcher_sha256=harness.digest_file(Path(__file__)),
              prepared_charge=charge(root),reservation_bytes=reservation,
              inventory=sorted(str(p.relative_to(root)) for p in root.rglob('*')))
    write_existing(out/'plan.json',plan,budget.file_limit)
    if charge(root)+budget.reserve>budget.cap:
        raise ValueError('control-file recount failed')
    return plan


def write_existing(path,value,limit):
    data=(dump(value)+'\n').encode()
    if len(data)>limit or path.stat().st_size:
        raise ValueError('control output is oversize or already published')
    with path.open('r+b') as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())


def protect_extents():
    """No deallocation or O_TRUNC can invalidate the fully allocated ranges."""
    if platform.machine()!='x86_64': raise RuntimeError('unsupported syscall architecture')
    filters=[(0x20,0,0,4),(0x15,1,0,0xc000003e),(6,0,0,0x80000000),
             (0x20,0,0,0),(0x35,0,1,0x40000000),(6,0,0,0x50001)]
    for nr in (76,77,85,285,319,425,426,427,437):
        filters.extend(((0x15,0,1,nr),(6,0,0,0x50001)))
    for nr,offset in ((2,24),(257,32)):
        filters.extend(((0x15,0,4,nr),(0x20,0,0,offset),
                        (0x45,0,1,os.O_TRUNC),(6,0,0,0x50001),(6,0,0,0x7fff0000)))
    filters.append((6,0,0,0x7fff0000))
    class Filter(ctypes.Structure):
        _fields_=[('code',ctypes.c_ushort),('jt',ctypes.c_ubyte),('jf',ctypes.c_ubyte),('k',ctypes.c_uint)]
    class Program(ctypes.Structure):
        _fields_=[('len',ctypes.c_ushort),('filter',ctypes.POINTER(Filter))]
    data=(Filter*len(filters))(*(Filter(*row) for row in filters)); program=Program(len(data),data)
    lib=ctypes.CDLL(None,use_errno=True)
    if lib.prctl(38,1,0,0,0) or lib.prctl(22,2,ctypes.byref(program),0,0):
        raise OSError(ctypes.get_errno(),'extent protection unavailable')


class IPCPool:
    """Create bounded shared-memory objects before denying ftruncate."""
    def __init__(self,count):
        self.context=harness.mp.get_context('fork')
        self.events=[self.context.Event() for _ in range(8)]
        self.values=[self.context.Value('q',0) for _ in range(2)]
        self.arrays=[self.context.RawArray('q',count*2) for _ in range(2)]
    def Event(self): return self.events.pop(0)
    def Value(self,*_): return self.values.pop(0)
    def RawArray(self,kind,count):
        value=self.arrays.pop(0)
        if kind!='q' or count!=len(value): raise ValueError('IPC declaration mismatch')
        return value
    def Process(self,*args,**kwargs): return self.context.Process(*args,**kwargs)


@contextmanager
def fixed_outputs(plan):
    out=Path(plan['out']); allowed={Path(p) for p in plan['files']}
    limit=plan['budget']['file_limit']; original_open=Path.open; original_mkdir=Path.mkdir
    original_capture=harness.MeasuredCapture
    dirs={out,*[p.parent for p in allowed]}; claimed=set()
    def opened(path,mode='r',*args,**kwargs):
        if any(c in mode for c in 'wax+'):
            if path not in allowed: raise PermissionError('undeclared scratch destination')
            if 'w' in mode or 'x' in mode:
                if path.stat().st_size: raise FileExistsError('refuse existing evidence overwrite')
                mode='r+b' if 'b' in mode else 'r+'
        return original_open(path,mode,*args,**kwargs)
    def mkdir(path,*args,**kwargs):
        if path in dirs:
            exist_ok=kwargs.get('exist_ok',args[2] if len(args)>2 else False)
            if not exist_ok:
                if path in claimed: raise FileExistsError(path)
                claimed.add(path)
            return None
        return original_mkdir(path,*args,**kwargs)
    def json_writer(path,value):
        if path not in allowed or path.with_suffix('.tmp') not in allowed:
            raise PermissionError('undeclared control output')
        # Outputs are fresh, single-publication files. The parent reads them only
        # after writer exit. Both staged and final bytes are flushed/fsynced.
        write_existing(path.with_suffix('.tmp'),value,limit)
        write_existing(path,value,limit)
    class FixedCapture(original_capture):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            if self.total or self.part!=1: raise ValueError('raw slot not pristine')
            self.part=0
    with patch.object(Path,'open',opened),patch.object(Path,'mkdir',mkdir), \
         patch.object(harness,'MeasuredCapture',FixedCapture), \
         patch.object(harness,'write_json',json_writer), \
         patch('crypto_paper.runtime.write_json',json_writer):
        yield


def pair(plan,prepared):
    out=Path(plan['out']); results=[]
    for number,loaded in enumerate((False,True),1):
        if 'budget' in plan:
            budget=Budget(**plan['budget'])
            if charge(Path(plan['root']))+budget.reserve>budget.cap or shutil.disk_usage(plan['root']).free<budget.floor+budget.reserve:
                raise ValueError('global reservation lost before arm')
        result=harness.trial(Path(plan['manifest']),out/(f'{number:02d}-'+('loaded' if loaded else 'idle')),
                             plan['seconds'],loaded,False,prepared)
        results.append({k:v for k,v in result.items() if k not in ('timing_rows','stage_services','failure_frames')})
        if not result['full_window_valid']: break
    value=dict(schema_version='scratch-guarded-pair-v1',actual_order=[r['mode'] for r in results],
               trials=results,full_window_series_valid=len(results)==2 and all(r['full_window_valid'] for r in results),
               operational_acceptance=False)
    harness.write_json(out/'series.json',value)
    return value


def sandbox_command(plan,python=sys.executable):
    cmd=['bwrap','--unshare-user','--unshare-pid','--unshare-net','--die-with-parent',
         '--cap-drop','ALL','--ro-bind','/','/','--proc','/proc',
         '--size',str(IPC),'--tmpfs','/dev/shm']
    for path in plan['files']:
        if Path(path).name!='plan.json': cmd+=['--bind',path,path]
    return cmd+['--setenv','TMPDIR',str(Path(plan['out'])/'temporary'),
                '--setenv','SQLITE_TMPDIR',str(Path(plan['out'])/'temporary'),
                '--setenv','PYTHONDONTWRITEBYTECODE','1','--',python,'-B','-m',
                'tools.scratch_envelope','--child-plan',str(Path(plan['out'])/'plan.json')]


def supervise(plan,deadline=180,grace=20,command=None):
    out=Path(plan['out'])
    with (out/'stdout.log').open('r+b') as stdout,(out/'stderr.log').open('r+b') as stderr:
        process=subprocess.Popen(command or sandbox_command(plan),stdout=stdout,stderr=stderr,
                                 stdin=subprocess.DEVNULL,start_new_session=True)
        timed_out=forced=False
        try: code=process.wait(timeout=deadline)
        except subprocess.TimeoutExpired:
            timed_out=True; os.killpg(process.pid,signal.SIGINT)
            try: code=process.wait(timeout=grace)
            except subprocess.TimeoutExpired:
                forced=True; os.killpg(process.pid,signal.SIGKILL); code=process.wait()
    budget=Budget(**plan['budget']); root=Path(plan['root'])
    inventory_ok=sorted(str(p.relative_to(root)) for p in root.rglob('*'))==plan['inventory']
    extents_ok=all(Path(p).stat().st_blocks*512==budget.file_limit and
                   Path(p).stat().st_size<=budget.file_limit for p in plan['files'])
    capacity_ok=charge(root)+budget.reserve<=budget.cap and shutil.disk_usage(root).free>=budget.floor+budget.reserve
    input_ok=harness.digest_file(Path(plan['manifest']))==plan['input_manifest_sha256']
    result=dict(returncode=code,timed_out=timed_out,forced=forced,
                inventory_unchanged=inventory_ok,reserved_extents_intact=extents_ok,
                global_reservation_intact=capacity_ok,input_manifest_unchanged=input_ok,
                success=code==0 and not timed_out and inventory_ok and extents_ok and capacity_ok and input_ok)
    write_existing(out/'guard.json',result,plan['budget']['file_limit'])
    return result


def child(plan):
    budget=Budget(**plan['budget']); budget.validate()
    if harness.digest_file(Path(__file__))!=plan['launcher_sha256'] or harness.digest_file(Path(harness.__file__))!=plan['harness_sha256']:
        raise ValueError('execution code changed')
    if harness.digest_file(Path(plan['manifest']))!=plan['input_manifest_sha256']:
        raise ValueError('retained input changed')
    prepared=harness.select_input(Path(plan['manifest']),plan['seconds'])
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    resource.setrlimit(resource.RLIMIT_FSIZE,(budget.file_limit,budget.file_limit))
    pool=IPCPool(len(prepared[2]))
    protect_extents()
    with fixed_outputs(plan),patch.object(harness.mp,'get_context',lambda mode:pool):
        result=pair(plan,prepared)
    return 0 if result['full_window_series_valid'] else 2


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--child-plan',type=Path)
    parser.add_argument('--root',type=Path)
    parser.add_argument('--manifest',type=Path)
    parser.add_argument('--out',type=Path)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    if args.child_plan:
        raise SystemExit(child(load(args.child_plan.read_bytes())))
    if not all((args.root,args.manifest,args.out)): parser.error('root, manifest and fresh out required')
    root=args.root.resolve()
    with (root/'.scratch-envelope.lock').open('a+b') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        plan=prepare(root,args.manifest,args.out)
        if args.execute:
            result=supervise(plan)
            raise SystemExit(0 if result['success'] else 2)
        print('Reservation prepared; execution requires explicit --execute after peer review.')


if __name__=='__main__': main()
