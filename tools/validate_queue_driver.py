"""Independent same-schedule fast-drain control; no collector or financial claims."""
import argparse
import asyncio
import multiprocessing as mp
from pathlib import Path
import socket
import sys
import time

PROJECT=Path(__file__).resolve().parents[1]
if str(PROJECT) not in sys.path: sys.path.insert(0,str(PROJECT))
from crypto_paper.data import sha
from crypto_paper.runtime import write_json,digest_file,code_hashes
from tools.replay_queue_load import select_input,producer,FakeWebSocket,DriverState,CONFIG,driver_fidelity,distributions,_cleanup


def validate(manifest,out,seconds):
    info,parts,schedule,identity=select_input(manifest,seconds)
    out.mkdir(parents=True,exist_ok=False)
    before={str(p):digest_file(p) for p in [manifest,manifest.parent/'ledger.sqlite3',*parts]}
    ctx=mp.get_context('fork');go=ctx.Event();ready=ctx.Event();stop=ctx.Event();start=ctx.Value('q',0)
    times=ctx.RawArray('q',len(schedule)*2);receiver,sender=socket.socketpair();receiver.setblocking(False)
    buffers=dict(send=sender.getsockopt(socket.SOL_SOCKET,socket.SO_SNDBUF),receive=receiver.getsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF))
    process=ctx.Process(target=producer,args=(sender,schedule,start,go,ready,stop,times,str(out/'producer.json')))
    state=DriverState();ws=FakeWebSocket(receiver,state,CONFIG['max_frame_bytes']);accepted=[];error=None
    process.start();sender.close()
    try:
        if not ready.wait(5):raise RuntimeError('producer not ready')
        async def drain():
            start.value=time.monotonic_ns()+CONFIG['producer_start_lead_ns'];go.set()
            async with asyncio.timeout(seconds+5):
                for i,row in enumerate(schedule):
                    wire=await ws.recv(decode=False)
                    meta=state.pending.popleft()
                    if meta['schedule_index']!=i or sha(wire)!=row['sha256']:raise ValueError('payload/order mismatch')
                    accepted.append(meta)
        asyncio.run(drain())
    except Exception as exc:error=repr(exc)
    finally:
        stop.set();go.set();cleanup=_cleanup(process);receiver.close()
    if cleanup['alive']:raise RuntimeError('producer alive after cleanup')
    rows=[dict(planned_ns=start.value+r['offset_ns'],send_start_ns=times[2*i],send_end_ns=times[2*i+1]) for i,r in enumerate(schedule)]
    fidelity=driver_fidelity(rows)
    unchanged=before=={str(p):digest_file(p) for p in [manifest,manifest.parent/'ledger.sqlite3',*parts]}
    if not unchanged:raise ValueError('sealed input changed')
    result=dict(scope='producer/socket fast-drain only; original collector/Capture/Session deliberately absent',
        source_manifest_sha256=before[str(manifest)],input_schedule_sha256=identity,harness_sha256=digest_file(PROJECT/'tools/replay_queue_load.py'),
        control_sha256=digest_file(Path(__file__)),package_hashes=code_hashes(),config=CONFIG,socket_buffers=buffers,
        seconds=seconds,scheduled_frames=len(schedule),sent_frames=sum(bool(r['send_end_ns']) for r in rows),received_frames=len(accepted),
        actual_payload_prefix_verified=True,complete_input=len(accepted)==len(schedule),driver=fidelity,
        read_lateness_ns=distributions([r['read_ns']-r['planned_ns'] for r in accepted]),
        error=error,cleanup=cleanup,source_unchanged=True,operational_acceptance=False,
        verdict='PASS' if error is None and len(accepted)==len(schedule) and fidelity['schedule_faithful'] else 'FAIL',
        limitations=['does not test capture/fsync/SQLite/CRC processing','does not emulate native WebSocket buffering','one independent control, not causal proof of earlier live failures'])
    write_json(out/'receipt.json',result)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--seconds',type=int,default=60)
    a=p.parse_args()
    if not 1<=a.seconds<=60:p.error('seconds must be1..60')
    validate(a.manifest,a.out,a.seconds)


if __name__=='__main__':main()
