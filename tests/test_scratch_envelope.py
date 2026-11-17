"""Reduced-size synthetic proofs for fixed slots, kernel denial and safe stops."""
import errno
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from crypto_paper.data import dump, load
from tools import scratch_envelope as guard
import test_replay_queue_load as fixtures


class ScratchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.source=fixtures.ReplayQueueTests().source(self.root)
        self.budget=guard.Budget(file_limit=guard.MIB,reserve=16*guard.MIB,cap=128*guard.MIB)

    def prepare(self):
        return guard.prepare(self.root,self.source,self.root/'pair',self.budget,seconds=1)

    def command(self,plan,body):
        cmd=guard.sandbox_command(plan)
        prefix=cmd[:cmd.index('--')+1]
        script="""import json,sys
from pathlib import Path
from tools import scratch_envelope as g
from crypto_paper.data import load
p=load(Path(sys.argv[1]).read_bytes())
original_pair=g.pair
def probe(plan,prepared):
"""+''.join('    '+line+'\n' for line in body.splitlines())+"""g.pair=probe
raise SystemExit(g.child(p))
"""
        return prefix+[sys.executable,'-B','-c',script,str(Path(plan['out'])/'plan.json')]

    def test_admission_includes_retained_inputs_both_arms_and_stop_reserve(self):
        self.assertEqual(guard.Budget().allowance,3758096384)
        self.assertEqual(guard.Budget().allowance+guard.Budget().reserve,4026531840)
        with patch.object(guard,'charge',return_value=self.budget.cap-self.budget.allowance-self.budget.reserve+1):
            with self.assertRaisesRegex(ValueError,'admission'):
                self.prepare()
        self.assertFalse((self.root/'pair').exists())
        with patch.object(guard.shutil,'disk_usage',return_value=type('Usage',(),{'free':self.budget.floor+self.budget.allowance+self.budget.reserve-1})()):
            with self.assertRaisesRegex(ValueError,'admission'): self.prepare()

    def test_slot_census_counts_compression_controls_and_temporary_files(self):
        plan=self.prepare(); files=list(map(Path,plan['files']))
        self.assertEqual(len(files),56)
        for arm in ('01-idle','02-loaded'):
            subset=[p for p in files if p.is_relative_to(self.root/'pair'/arm)]
            self.assertEqual(len(subset),20)
            self.assertIn(self.root/'pair'/arm/'compression.partial.xz',subset)
        self.assertEqual(len([p for p in files if p.parent.name=='temporary']),8)
        self.assertTrue(all(p.stat().st_blocks*512==self.budget.file_limit for p in files))
        self.assertGreaterEqual(guard.charge(self.root),56*self.budget.file_limit)

    def test_symlinks_existing_evidence_and_relaxed_limits_are_rejected(self):
        (self.root/'link').symlink_to(self.source)
        with self.assertRaisesRegex(ValueError,'non-regular'): self.prepare()
        (self.root/'link').unlink()
        with self.assertRaisesRegex(ValueError,'fresh output'):
            guard.prepare(self.root,self.source,self.source.parent,self.budget)
        for kwargs in ({'cap':guard.G+1},{'floor':guard.F-1},{'file_limit':65*guard.MIB}):
            with self.assertRaises(ValueError): guard.Budget(**kwargs).validate()

    def test_same_guard_runs_both_synthetic_arms_without_rule_changes(self):
        plan=self.prepare()
        before={p:p.read_bytes() for p in self.source.parent.rglob('*') if p.is_file()}
        result=guard.supervise(plan,deadline=25,grace=3)
        if not result['success']:
            self.fail((self.root/'pair/stderr.log').read_text())
        series=load((self.root/'pair/series.json').read_bytes())
        self.assertEqual(series['actual_order'],['idle','loaded'])
        self.assertTrue(result['reserved_extents_intact'])
        self.assertTrue(result['inventory_unchanged'])
        self.assertTrue(result['global_reservation_intact'])
        self.assertEqual(before,{p:p.read_bytes() for p in before})
        evidence={p:p.read_bytes() for p in (self.root/'pair').rglob('*') if p.is_file()}
        with patch.object(guard.subprocess,'Popen') as launch:
            with self.assertRaisesRegex(ValueError,'already published'):
                guard.supervise(plan)
            launch.assert_not_called()
        self.assertEqual(evidence,{p:p.read_bytes() for p in evidence})
        for arm in series['trials']:
            self.assertEqual(arm['own_raw_ordered_events_and_account_replay'],'PASS')
            self.assertFalse(arm['clock_valid'])
            self.assertEqual(arm['config'],guard.harness.CONFIG)
            self.assertTrue(all(not p['alive'] for p in arm['process_cleanup']))

    def test_extra_and_sqlite_temp_output_are_denied_by_kernel(self):
        plan=self.prepare()
        body="""import os,sqlite3
errors=[]
for name in ('01-idle/extra.bin','temporary/undeclared-sqlite.tmp','02-loaded/extra.bin'):
    try:
        fd=os.open(str(Path(plan['out'])/name),os.O_CREAT|os.O_WRONLY,0o600)
    except OSError: errors.append(name)
    else: os.close(fd)
try:
    db=sqlite3.connect(str(Path(plan['out'])/'temporary/unplanned.sqlite3'))
except sqlite3.OperationalError: errors.append('sqlite-c-vfs')
else: db.close()
print(json.dumps({'denied':len(errors)}),flush=True)
return {'full_window_series_valid':len(errors)==4}"""
        result=guard.supervise(plan,command=self.command(plan,body),deadline=10,grace=2)
        self.assertTrue(result['success'])
        self.assertEqual(json.loads((self.root/'pair/stdout.log').read_text()),{'denied':4})

    def test_partial_compression_limit_and_deallocation_cannot_escape_reservation(self):
        plan=self.prepare()
        body="""import os,signal
signal.signal(signal.SIGXFSZ,signal.SIG_IGN)
p=Path(plan['out'])/'02-loaded/compression.partial.xz'
fd=os.open(str(p),os.O_RDWR)
limit=plan['budget']['file_limit']
os.pwrite(fd,b'partial',0)
blocked=0
for operation in (lambda:os.ftruncate(fd,0),lambda:os.open(str(p),os.O_WRONLY|os.O_TRUNC)):
    try: operation()
    except OSError: blocked+=1
try: os.pwrite(fd,b'X',limit)
except OSError: blocked+=1
os.fsync(fd); os.close(fd)
print(json.dumps({'blocked':blocked,'prefix':p.read_bytes().decode()}),flush=True)
return {'full_window_series_valid':blocked==3}"""
        result=guard.supervise(plan,command=self.command(plan,body),deadline=10,grace=2)
        self.assertTrue(result['success'])
        receipt=json.loads((self.root/'pair/stdout.log').read_text())
        self.assertEqual(receipt,{'blocked':3,'prefix':'partial'})

    def test_budget_stop_or_incomplete_idle_never_calls_second_arm(self):
        plan={'out':'unused','manifest':'unused','seconds':1}
        with patch.object(guard.harness,'trial',side_effect=OSError(errno.EFBIG,'file cap')) as trial:
            with self.assertRaises(OSError): guard.pair(plan,None)
            self.assertEqual(trial.call_count,1)
        with patch.object(guard.harness,'trial',return_value={'full_window_valid':False,'mode':'idle'}) as trial, \
             patch.object(guard.harness,'write_json'):
            result=guard.pair(plan,None)
            self.assertEqual(trial.call_count,1)
            self.assertEqual(result['actual_order'],['idle'])

    def test_real_compressor_oversize_keeps_partial_and_no_success_receipt(self):
        import random
        original=random.Random(123).randbytes(96*1024)
        (self.root/'noise').write_bytes(original)
        self.budget=guard.Budget(file_limit=64*1024,reserve=16*guard.MIB,cap=64*guard.MIB)
        plan=self.prepare()
        body="""import os,signal,threading
from types import SimpleNamespace
signal.signal(signal.SIGXFSZ,signal.SIG_IGN)
gate=threading.Event(); gate.set()
base=Path(plan['out'])/'02-loaded'
try:
    g.harness.compression_worker([str(Path(plan['root'])/'noise')],str(base/'compression.partial.xz'),
        SimpleNamespace(value=0),gate,threading.Event(),threading.Event(),str(base/'compression.json'))
except OSError as error:
    passed=error.errno==27 and 0<(base/'compression.partial.xz').stat().st_size<=plan['budget']['file_limit']
else: passed=False
print(json.dumps({'cap_stop':passed,'receipt_bytes':(base/'compression.json').stat().st_size}),flush=True)
return {'full_window_series_valid':passed}"""
        result=guard.supervise(plan,command=self.command(plan,body),deadline=10,grace=2)
        self.assertTrue(result['success'])
        self.assertEqual(json.loads((self.root/'pair/stdout.log').read_text()),{'cap_stop':True,'receipt_bytes':0})
        self.assertEqual((self.root/'noise').read_bytes(),original)

    def test_forced_cleanup_is_failure_and_preserves_evidence(self):
        plan=self.prepare()
        partial=self.root/'pair/01-idle/compression.partial.xz'
        with partial.open('r+b') as stream:
            stream.write(b'partial'); stream.flush(); os.fsync(stream.fileno())
        script="import signal,time; signal.signal(signal.SIGINT,signal.SIG_IGN); print('READY',flush=True); time.sleep(30)"
        result=guard.supervise(plan,command=[sys.executable,'-c',script],deadline=1,grace=.1)
        self.assertTrue(result['timed_out']); self.assertTrue(result['forced'])
        self.assertFalse(result['success'])
        self.assertEqual(partial.read_bytes(),b'partial')
        self.assertEqual((self.root/'pair/02-loaded/raw/000001.jsonl').stat().st_size,0)

    def test_worker_failure_latch_blocks_second_arm_with_signal_ignored(self):
        plan=self.prepare()
        body="""import os,signal
signal.signal(signal.SIGUSR1,signal.SIG_IGN)
base=Path(plan['out'])/'01-idle/compression.partial.xz'
def cap_worker():
    fd=os.open(str(base),os.O_RDWR)
    os.pwrite(fd,b'partial',0)
    os.pwrite(fd,b'X',plan['budget']['file_limit'])
def trial(*args,**kwargs):
    worker=g.harness.mp.get_context('fork').Process(target=cap_worker,args=())
    worker.start()
    try: worker.join(5)
    finally:
        worker.join(1)
        if worker.is_alive(): worker.terminate(); worker.join()
    return {'mode':'idle','full_window_valid':True}
g.harness.trial=trial
return original_pair(plan,prepared)"""
        result=guard.supervise(plan,command=self.command(plan,body),deadline=10,grace=2)
        self.assertFalse(result['success'])
        self.assertFalse(result['timed_out'])
        self.assertEqual((self.root/'pair/01-idle/compression.partial.xz').read_bytes(),b'partial')
        self.assertEqual((self.root/'pair/02-loaded/raw/000001.jsonl').stat().st_size,0)

    def test_guarded_full_journal_keeps_nonzero_fees_and_rollback(self):
        plan=self.prepare()
        body="""from crypto_paper.engine import Engine
from crypto_paper.data import D,NANO
from crypto_paper.verify import UTC,META,book_at
s=g.harness.MeasuredSession(Path(plan['out'])/'01-idle','synthetic',g.harness.DriverState())
e=Engine(s.ledger); f={'idx':1,'utc':UTC,'mono':0}
try:
    with s.ledger.transaction(1,'one'): e.order('buy',D('.1'),book_at(asks={'100':'1'}),META,f)
    try:
        with s.ledger.transaction(2,'two'):
            e.on_book(book_at(2,asks={'100':'1'}),META,f|{'idx':2,'mono':NANO})
            raise RuntimeError('rollback')
    except RuntimeError: pass
    assert e.val('cash')==D('10000') and e.val('btc')==0
    with s.ledger.transaction(2,'two'):
        e.on_book(book_at(2,asks={'100':'1'}),META,f|{'idx':2,'mono':NANO})
        e.order('sell',D('0'),book_at(2,asks={'100':'1'}),META,f|{'idx':2,'mono':NANO})
    with s.ledger.transaction(3,'three'):
        e.on_book(book_at(3,asks={'100':'1'},bids={'99.9':'1'}),META,f|{'idx':3,'mono':2*NANO})
    fills=[load(p) for _,_,kind,p in s.ledger.sequence() if kind=='fill']
    assert sum(D(x['fee']) for x in fills)==D('1.5992')
    assert e.val('cash')==e.val('nav')==D('9998.3008')
    assert e.val('realized')==D('-1.6992') and e.val('btc')==0
    assert s.ledger.reconcile()
    assert s.ledger.db.execute('PRAGMA synchronous').fetchone()==(2,)
    assert s.ledger.db.execute('PRAGMA journal_mode').fetchone()==('persist',)
finally: s.close()
return {'full_window_series_valid':True}"""
        result=guard.supervise(plan,command=self.command(plan,body),deadline=10,grace=2)
        if not result['success']: self.fail((self.root/'pair/stderr.log').read_text())

    def test_control_publication_fsyncs_and_refuses_existing_evidence(self):
        plan=self.prepare(); target=self.root/'pair/series.json'
        with guard.fixed_outputs(plan):
            with patch.object(os,'fsync',wraps=os.fsync) as sync:
                guard.harness.write_json(target,{'synthetic':True})
                self.assertEqual(sync.call_count,2)
            with self.assertRaisesRegex(ValueError,'already published'):
                guard.harness.write_json(target,{'overwrite':True})
        self.assertEqual(load(target.read_bytes()),{'synthetic':True})

    def test_deadline_preserves_partial_outputs_and_never_reports_success(self):
        plan=self.prepare()
        body="""import os,time,signal
p=Path(plan['out'])/'01-idle/compression.partial.xz'
with p.open('r+b') as stream:
    stream.write(b'partial'); stream.flush(); os.fsync(stream.fileno())
signal.signal(signal.SIGINT,lambda *_:sys.exit(0))
print('READY',flush=True)
while True: time.sleep(.01)
return {'full_window_series_valid':True}"""
        result=guard.supervise(plan,command=self.command(plan,body),deadline=2,grace=2)
        self.assertTrue(result['timed_out'])
        self.assertFalse(result['success'])
        self.assertFalse(result['forced'])
        self.assertEqual((self.root/'pair/01-idle/compression.partial.xz').read_bytes(),b'partial')
        self.assertEqual((self.root/'pair/02-loaded/raw/000001.jsonl').stat().st_size,0)


if __name__=='__main__': unittest.main()
