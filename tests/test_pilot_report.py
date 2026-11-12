"""Synthetic acceptance cases from architecture handoff 13fb024; no market data."""
import copy
from decimal import Decimal as D
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from crypto_paper.data import NANO, dump, parse_time, stamp
from crypto_paper.pilot_report import HOUR, project

T0 = parse_time("2026-01-01T00:00:00Z")


def snapshot(frame, utc, cash="10000", btc="0", **extra):
    return {"frame":frame,"utc":utc,"received_utc":utc,"cash":cash,"btc":btc,
            "mark_utc":utc,"mark_received_utc":utc,"bid":"100000",
            "book_valid":True,"clock_valid":True,"journal_reconciled":True,
            "last_observed_nav":cash,**extra}


def case(day=False):
    end = T0+(24 if day else 6)*HOUR
    return {"schema_version":"pilot-snapshot-v1","mode":"fixture","run_id":"synthetic",
            "policy":"daily-sma50-v1","scenario":"base","kind":"utc_day" if day else "six_hour",
            "pilot_start":T0,"interval_start":T0,"interval_end":end,"revision":0,
            "snapshots":[snapshot(1,T0-1),snapshot(2,end-1)],"committed_frame":2,
            "coverage":{"ready":(end-T0)//NANO,"nonready":0,"missing":0},
            "fills":[],"opening_peak":"10000","code_hashes":{"fixture":"synthetic"},
            "config_hash":"synthetic","manifest_hash":"synthetic","unresolved_gaps":[],"integrity":"PASS","replay":"PASS","risk_violations":[],
            "locks":[],"dust":"0","decisions":{"expected":0,"eligible":0,"timely":0,"SKIP":0},
            "reconciliation":{"status":"SYNTHETIC"},"paired_baselines":{"pair_count":0,"missing":1},
            "completed_work":["Synthetic projector acceptance case"]}


class PilotReportTests(unittest.TestCase):
    def report(self, s):
        return project(s,s["interval_end"])

    def test_fee_and_liquidation_reserve_are_not_deducted_twice(self):
        s=case()
        s["snapshots"][-1].update(cash="9899.20",btc="0.001")
        s["fills"]=[{"utc":T0+NANO,"received_utc":T0+NANO,"frame":2,"fee_usd":".80"}]
        r=self.report(s)
        self.assertEqual(r["paid_fees_usd"],D('.80'))
        self.assertEqual(r["end"]["exit_reserve_usd"],D('.80'))
        self.assertEqual(r["end"]["nav"],D('9998.40'))
        self.assertEqual(r["interval_net"]["usd"],D('-1.60'))
        self.assertEqual(r["interval_net"]["percent"],D('-.016'))

    def test_six_hour_and_generation_delay(self):
        s=case(); s["snapshots"][-1]["cash"]="10020"
        r=project(s,s["interval_end"]+HOUR)
        self.assertEqual(r["interval_net"]["usd"],20)
        self.assertEqual(r["interval_net"]["percent"],D('.2'))
        self.assertEqual((r["report_index"],r["report_count"],r["elapsed_hours"]),(1,28,6))
        self.assertTrue(r["delayed"])

    def test_stale_boundary_cannot_be_repaired_by_later_quote(self):
        s=case(); b=s["interval_end"]
        s["snapshots"][-1].update(btc=".001",mark_utc=b-2001*1000000)
        s["snapshots"].append(snapshot(3,b+100000000,cash="9999",btc=".001"))
        s["committed_frame"]=3
        r=self.report(s)
        self.assertEqual(r["end"]["reason"],"BOOK_STALE")
        self.assertIsNone(r["interval_net"]["usd"])
        s["snapshots"][1]["mark_utc"]=b-2000*1000000
        self.assertIsNotNone(self.report(s)["end"]["nav"])

    def test_clock_invalid_and_missing_mark(self):
        s=case(); s["snapshots"][-1].update(btc=".001",clock_valid=False)
        r=self.report(s)
        self.assertEqual(r["end"]["reason"],"CLOCK_INVALID")
        self.assertIsNone(r["end"]["mark_age_ms"])
        s["snapshots"][-1].update(clock_valid=True,mark_utc=None)
        self.assertEqual(self.report(s)["end"]["reason"],"BOOK_MISSING")

    def test_missing_time_stays_in_denominator(self):
        s=case(); s["coverage"]={"ready":21000,"nonready":300,"missing":300}
        r=self.report(s)
        self.assertEqual(r["coverage"]["expected"],21600)
        self.assertTrue(r["coverage"]["degraded"])
        self.assertTrue(D('97.2222') < r["coverage"]["ready_percent"] < D('97.2223'))
        self.assertIn("COVERAGE_UNRESOLVED",r["candidate_reasons"])

    def test_invalid_open_is_not_replaced_by_old_valid_nav(self):
        s=case(); s["snapshots"][0]["journal_reconciled"]=False
        self.assertIsNone(self.report(s)["interval_net"]["usd"])

    def test_complete_utc_day_uses_own_open_not_inception(self):
        s=case(True); s["pilot_start"]-=24*HOUR
        s["snapshots"][0]["cash"]="10200"; s["snapshots"][-1]["cash"]="15300"
        s["snapshots"].insert(0,snapshot(1,s["pilot_start"]-1))
        for i,x in enumerate(s["snapshots"],1): x["frame"]=i
        s["committed_frame"]=3
        r=self.report(s)
        self.assertEqual(r["interval_net"]["usd"],5100)
        self.assertEqual(r["interval_net"]["percent"],50)
        self.assertEqual(r["inception_net"]["percent"],53)
        self.assertEqual(r["candidate_status"],"candidate_pending_review")
        self.assertFalse(r["real_alert_sent"])
        self.assertEqual(r["delivery_status"],"NOT_ATTEMPTED")

    def test_alert_rejection_gates(self):
        for key,value,reason in [('integrity','FAIL','INTEGRITY_UNVERIFIED'),
                                 ('replay','FAIL','REPLAY_UNVERIFIED'),
                                 ('risk_violations',['synthetic'],'RISK_VIOLATION'),
                                 ('unresolved_gaps',['synthetic'],'COVERAGE_UNRESOLVED')]:
            s=case(True); s["snapshots"][-1]["cash"]="15000"; s[key]=value
            self.assertIn(reason,self.report(s)["candidate_reasons"])
        s=case(True); s["interval_start"]+=HOUR
        with self.assertRaises(ValueError): self.report(s)

    def test_strict_cutoff_for_fills_and_receive_times(self):
        s=case(); b=s["interval_end"]
        s["fills"]=[{"utc":b,"received_utc":b,"frame":2,"fee_usd":"100"}]
        s["snapshots"][-1]["received_utc"]=b+1
        r=self.report(s)
        self.assertEqual(r["paid_fees_usd"],0)
        self.assertEqual(r["end"]["frame"],1)

    def test_retries_have_same_identity_and_corrections_are_audited(self):
        s=case(); a=self.report(s); b=project(s,s["interval_end"]+HOUR)
        self.assertEqual(a["report_id"],b["report_id"])
        self.assertEqual(a["source_sha256"],b["source_sha256"])
        s["revision"]=1
        with self.assertRaises(ValueError): self.report(s)
        s.update(correction_reason="Synthetic correction",audit_link="synthetic:previous")
        self.assertNotEqual(a["report_id"],self.report(s)["report_id"])

    def test_input_is_unchanged_and_invalid_inputs_fail_closed(self):
        s=case(); before=copy.deepcopy(s); self.report(s); self.assertEqual(before,s)
        for key,value in [('mode','production'),('committed_frame',1),('opening_peak',float('nan'))]:
            bad=copy.deepcopy(s); bad[key]=value
            with self.assertRaises(ValueError): self.report(bad)
        s["coverage"]["missing"]=1
        with self.assertRaises(ValueError): self.report(s)

    def test_observed_max_drawdown_and_unknown_current(self):
        s=case(); b=s["interval_end"]
        s["snapshots"]=[s["snapshots"][0],snapshot(2,T0+NANO,cash="11000"),
                        snapshot(3,T0+2*NANO,cash="9900"),snapshot(4,b-1,cash="11000")]
        s["committed_frame"]=4
        self.assertEqual(self.report(s)["observed_max_drawdown_percent"],10)
        s["snapshots"][-1].update(btc=".001",clock_valid=False)
        self.assertEqual(self.report(s)["drawdown_current"],"UNKNOWN")

    def test_cli_reads_only_and_never_overwrites_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'synthetic.json'; out=Path(tmp)/'report.json'
            source.write_text(dump(case()))
            original=source.read_bytes()
            cmd=[sys.executable,'-m','crypto_paper.pilot_report','--snapshot',str(source),
                 '--generated-at',stamp(case()["interval_end"]),'--out',str(out)]
            subprocess.run(cmd,check=True,capture_output=True)
            first=out.read_bytes()
            result=subprocess.run(cmd,capture_output=True)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(first,out.read_bytes()); self.assertEqual(original,source.read_bytes())
            self.assertFalse(json.loads(first)["real_alert_sent"])


if __name__ == '__main__':
    unittest.main()
