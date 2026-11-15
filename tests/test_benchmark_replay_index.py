"""Experimental index invariance, with actual synthetic fills and fee arithmetic."""
from pathlib import Path
import tempfile
import unittest

from crypto_paper import capture_report as projector
from crypto_paper.data import D, NANO, dump, load
from crypto_paper.engine import Engine
from crypto_paper.runtime import Capture, Session, manifest, digest_file
from crypto_paper.verify import UTC, META, book_at
from tools.benchmark_replay_index import audit, benchmark, experimental_ledgers


class ReplayIndexTests(unittest.TestCase):
    def sealed(self, root):
        out=root/'sealed'; out.mkdir()
        s=Session(out,'synthetic','observe'); cap=Capture(out,'synthetic')
        try:
            for kind,offset,extra in [('clock',0,{'offset_ms':[]}),
                                      ('run_begin',1,{'duration':600}),
                                      ('sample',2,{}),('shutdown',3,{})]:
                s.handle(cap.put(kind,utc=UTC+offset*NANO,mono=offset*NANO,**extra))
        finally:
            cap.close(); s.close()
        manifest(out,'synthetic','observe',UTC,state='DIAGNOSTIC')
        return out/'manifest.json'

    def test_entire_projector_variants_match_and_keep_source_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=self.sealed(Path(tmp))
            before={x:digest_file(x) for x in p.parent.rglob('*') if x.is_file()}
            original=projector.Ledger
            result=benchmark(p,UTC,UTC+600*NANO)
            self.assertIs(projector.Ledger,original)
            self.assertTrue(result['identical_ordered_events'])
            self.assertTrue(result['identical_final_account'])
            self.assertEqual(result['variants'][0]['ledger_audit'],result['variants'][1]['ledger_audit'])
            self.assertEqual(before,{x:digest_file(x) for x in before})
            self.assertFalse(result['operational_acceptance'])
            self.assertEqual([v['readback'] for v in result['variants']],['PASS','PASS'])

    def test_index_keeps_real_fill_fee_and_rollback_accounting_identical(self):
        results=[]
        for indexed in (False,True):
            summaries={}
            with experimental_ledgers(indexed,summaries):
                ledger=projector.Ledger(':memory:'); engine=Engine(ledger)
                try:
                    book=book_at(asks={'100':'1'})
                    frame={'idx':1,'utc':UTC,'mono':0}
                    with ledger.transaction(1,'synthetic-one'):
                        engine.order('buy',D('.1'),book,META,frame)
                    book=book_at(2,asks={'100':'1'})
                    with self.assertRaisesRegex(RuntimeError,'rollback'):
                        with ledger.transaction(2,'synthetic-two'):
                            engine.on_book(book,META,frame|{'idx':2,'mono':NANO})
                            raise RuntimeError('rollback')
                    self.assertEqual(engine.val('cash'),D('10000'))
                    self.assertEqual(engine.val('btc'),D('0'))
                    self.assertEqual(ledger.db.execute("SELECT count(*) FROM events WHERE kind='fill'").fetchone()[0],0)
                    book=book_at(2,asks={'100':'1'})
                    with ledger.transaction(2,'synthetic-two'):
                        engine.on_book(book,META,frame|{'idx':2,'mono':NANO})
                        engine.order('sell',D('0'),book,META,frame|{'idx':2,'mono':NANO})
                    # Literal arithmetic independent of the production accounting helper:
                    # buy 1 BTC for100, paid fee .8; bid99.9, exit reserve .7992.
                    self.assertEqual(engine.val('cash'),D('9899.2'))
                    self.assertEqual(engine.val('btc'),D('1'))
                    self.assertEqual(engine.val('nav'),D('9998.3008'))
                    fee=ledger.db.execute("SELECT payload FROM events WHERE kind='fill'").fetchone()[0]
                    self.assertEqual(D(load(fee)['fee']),D('.8'))
                    book=book_at(3,asks={'100':'1'},bids={'99.9':'1'})
                    with ledger.transaction(3,'synthetic-three'):
                        engine.on_book(book,META,frame|{'idx':3,'mono':2*NANO})
                    # Closing proceeds=99.9-.7992; cost basis=100+.8.
                    self.assertEqual(engine.val('cash'),D('9998.3008'))
                    self.assertEqual(engine.val('nav'),D('9998.3008'))
                    self.assertEqual(engine.val('btc'),D('0'))
                    self.assertEqual(engine.val('cost'),D('0'))
                    self.assertEqual(engine.val('realized'),D('-1.6992'))
                    fills=[load(r[0]) for r in ledger.db.execute("SELECT payload FROM events WHERE kind='fill' ORDER BY seq")]
                    self.assertEqual([f['side'] for f in fills],['buy','sell'])
                    self.assertEqual(D(fills[1]['fee']),D('.7992'))
                    self.assertEqual(sum(D(f['fee']) for f in fills),D('1.5992'))
                    self.assertTrue(ledger.reconcile())
                    index_names={r[1] for r in ledger.db.execute("PRAGMA index_list(events)")}
                    self.assertEqual('experimental_events_frame' in index_names,indexed)
                finally:
                    ledger.close()
            results.append(summaries['rebuilt'])
        self.assertEqual(results[0],results[1])
        self.assertEqual(results[0]['event_counts']['fill'],2)
        self.assertGreater(results[0]['financial_event_count'],0)

    def test_tampering_is_rejected_without_replacing_source_build_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=self.sealed(Path(tmp)); info=load(p.read_bytes())
            info['code_hashes']['engine.py']='0'*64; p.write_text(dump(info))
            with self.assertRaisesRegex(ValueError,'recorded code'): benchmark(p,UTC,UTC+600*NANO)
            # Restore code hashes through a newly sealed manifest, then corrupt raw data.
            manifest(p.parent,'synthetic','observe',UTC,state='DIAGNOSTIC')
            part=p.parent/'raw/000001.jsonl'; part.write_bytes(part.read_bytes()+b'corrupt')
            with self.assertRaisesRegex(ValueError,'invalid manifest part'): benchmark(p,UTC,UTC+600*NANO)

    def test_factory_is_restored_on_replay_failure(self):
        original=projector.Ledger
        with self.assertRaisesRegex(RuntimeError,'synthetic failure'):
            with experimental_ledgers(True,{}):
                self.assertIsNot(projector.Ledger,original)
                raise RuntimeError('synthetic failure')
        self.assertIs(projector.Ledger,original)


if __name__ == '__main__': unittest.main()
