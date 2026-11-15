"""Same synthetic event stream compares diagnostic continuity to production halts."""
import tempfile
import unittest
from pathlib import Path

from crypto_paper.data import NANO, dump
from crypto_paper.diagnostic import DiagnosticBook
from crypto_paper.runtime import Capture, Session
from crypto_paper.verify import market, UTC


class DiagnosticTests(unittest.TestCase):
    def test_rejected_clock_leaves_diagnostics_live_and_production_halted(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=Session(Path(tmp),'synthetic','observe'); c=Capture(Path(tmp),'synthetic'); d=DiagnosticBook()
            def emit(kind,wire=b'',**kw):
                f=c.put(kind,wire,utc=UTC+c.idx*NANO,mono=c.idx*NANO,**kw); s.handle(f); d.handle(f); return f
            try:
                emit('connect',epoch=1)
                emit('ws',dump(market()).encode(),epoch=1)
                self.assertEqual(s.book.state,'READY'); self.assertEqual(d.book.state,'READY')
                emit('clock',offset_ms=[])
                self.assertEqual(s.book.state,'STALE'); self.assertEqual(d.book.state,'READY')
                update=market(); update['type']='update'
                emit('ws',dump(update).encode(),epoch=1)
                self.assertEqual(d.good,2); self.assertEqual(d.errors,0)
                self.assertFalse(s.clock); self.assertFalse(s.ready(s.last))
                self.assertEqual(s.ledger.db.execute("SELECT count(*) FROM events WHERE kind='fill'").fetchone()[0],0)
                self.assertEqual(d.metrics()['disconnects_by_origin'],{})
            finally: c.close(); s.close()

    def test_real_disconnect_and_bad_crc_require_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            c=Capture(Path(tmp),'synthetic'); d=DiagnosticBook()
            def emit(kind,wire=b'',**kw):
                f=c.put(kind,wire,utc=UTC+c.idx*NANO,mono=c.idx*NANO,**kw); d.handle(f); return f
            try:
                emit('connect',epoch=1); emit('ws',dump(market()).encode(),epoch=1)
                f=emit('disconnect',epoch=1,origin='induced',forced=True,force_mono=2*NANO)
                self.assertEqual(d.book.state,'STALE')
                emit('connect',epoch=2); emit('ws',dump(market()).encode(),epoch=2)
                self.assertEqual(d.recoveries_ms,[2000])
                bad=market(); bad['type']='update'; bad['data'][0]['checksum']+=1
                emit('ws',dump(bad).encode(),epoch=2)
                self.assertEqual(d.errors,1); self.assertEqual(d.book.state,'STALE')
                emit('disconnect',epoch=2,origin='feed_validation')
                emit('connect',epoch=3); emit('ws',dump(market()).encode(),epoch=3)
                self.assertEqual(d.book.state,'READY')
                self.assertEqual(d.metrics()['disconnects_by_origin'],{'induced':1,'feed_validation':1})
            finally: c.close()


if __name__ == '__main__': unittest.main()
