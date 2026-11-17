"""Exploratory bar-only proxy; no live execution or production acceptance."""
from decimal import Decimal as D, getcontext
from datetime import datetime, timezone, timedelta
import json,sys,urllib.request,unittest
from pathlib import Path
getcontext().prec=34
DAY=86400
START=int(datetime(2026,6,25,tzinfo=timezone.utc).timestamp())
END=int(datetime(2026,11,16,tzinfo=timezone.utc).timestamp())
def validate(rows):
    times=[r[0] for r in rows]
    if len(times)!=len(set(times)) or times!=sorted(times): raise ValueError('duplicate/unordered')
    for a,b in zip(times,times[1:]):
        if b-a!=DAY: raise ValueError('gap')
    for r in rows:
        if r[0]%DAY: raise ValueError('off-grid')
        o,h,l,c=map(D,r[1:5])
        if not all(x.is_finite() and x>0 for x in (o,h,l,c)) or not l<=min(o,c)<=max(o,c)<=h: raise ValueError('OHLC')
    selected=[r for r in rows if START<=r[0]<END]
    if [r[0] for r in selected]!=list(range(START,END,DAY)): raise ValueError('fixed holdout unavailable')
    first=times.index(START)
    if first<51: raise ValueError('warmup unavailable')
    return first

def signal(rows,i):
    closes=[D(r[4]) for r in rows[i-51:i-1]]
    if len(closes)!=50: raise ValueError('warmup')
    return closes[-1]>sum(closes)/50

def nav(c,q,p,f,s): return c+q*p*(1-s)*(1-f)
def size(c,q,p,f,s):
    a=p*(1+s)*(1+f);m=p*(1-s)*(1-f);n=c+q*m
    return max(D(0),min(c/a,D('.025')*n/a,(D('.10')*n-a*q)/(a+D('.10')*(a-m))))
def latch(n,peak):return n<=D('.96')*peak

def evaluate(rows,policy,f,s):
    first=validate(rows);c=D(10000);q=D(0);peak=D(10000);dd=D(0);fees=D(0);turn=D(0);fills=0;buys=0;locked=False;built=False;weights=[]
    def sample(p):
        nonlocal peak,dd,locked
        n=nav(c,q,p,f,s);peak=max(peak,n);dd=max(dd,1-n/peak)
        if latch(n,peak):locked=True
        weights.append(q*p/n)
        return n
    def sell(x,p):
        nonlocal c,q,fees,turn,fills
        if x<=0:return
        notional=x*p*(1-s);c+=notional*(1-f);q-=x;fees+=notional*f;turn+=notional;fills+=1
    for i in range(first,first+144):
        p=D(rows[i][1]);close=D(rows[i][4]);opening=sample(p)
        on=(policy=='hold' or (policy=='sma50' and signal(rows,i))) and not locked
        a=p*(1+s)*(1+f)
        if policy!='cash':
            if not on:sell(q,p)
            else:
                n=nav(c,q,p,f,s)
                sell(max(D(0),q-D('.10')*n/a),p)
                if policy=='sma50' or not built:
                    x=size(c,q,p,f,s)
                    if x>0:
                        notional=x*p*(1+s);c-=notional*(1+f);q+=x;fees+=notional*f;turn+=notional;fills+=1;buys+=1
                    if policy=='hold' and abs(D('.10')*nav(c,q,p,f,s)-q*a)<=D('1e-20'):built=True
        sample(p)
        ending=sample(close)
        if ending<=D('.99')*opening:locked=True
    final=nav(c,q,D(rows[first+143][4]),f,s)
    return dict(policy=policy,final_nav=str(final),net_usd=str(final-10000),net_pct=str(100*(final/10000-1)),sampled_drawdown_pct=str(dd*100),paid_fees=str(fees),exit_reserve=str(q*D(rows[first+143][4])*(1-(1-s)*(1-f))),turnover=str(turn),fills=fills,buy_fills=buys,mean_gross_marked_weight_pct=str(sum(weights)/len(weights)*100),max_gross_marked_weight_pct=str(max(weights)*100),locked=locked,hold_built=built,cash=str(c),btc=str(q))

class Tests(unittest.TestCase):
    def fixture(self):
        return [[START+(i-60)*DAY,'100','100','100','100'] for i in range(204)]
    def test_fee_roundtrip(self):
        f=D('.008');c=D(1000)-100*(1+f)
        self.assertEqual(nav(c,D(1),D(100),f,D(0)),D('998.4'))
        self.assertEqual(c+100*(1-f),D('998.4'))
    def test_cash(self):
        r=evaluate(self.fixture(),'cash',D('.008'),D(0));self.assertEqual(D(r['final_nav']),10000);self.assertEqual(D(r['sampled_drawdown_pct']),0);self.assertEqual(r['fills'],0)
    def test_no_leak(self):
        rows=self.fixture();i=60;self.assertFalse(signal(rows,i))
        rows[i][4]='100000';rows[i-1][4]='100000';self.assertFalse(signal(rows,i))
        rows[i-2][4]='101';self.assertTrue(signal(rows,i))
    def test_caps(self):
        c=D(10000);q=D(0);p=D(100);f=D('.008');s=D(0);a=p*(1+f)
        for _ in range(6):
            n=nav(c,q,p,f,s);x=size(c,q,p,f,s);self.assertLessEqual(x*a,D('.025')*n+D('1e-25'));c-=x*a;q+=x
            self.assertGreaterEqual(c,0);self.assertLessEqual(q*a,D('.10')*nav(c,q,p,f,s)+D('1e-25'))
    def test_missing_duplicate(self):
        rows=self.fixture()
        with self.assertRaises(ValueError):validate(rows[:-1])
        with self.assertRaises(ValueError):validate(rows+[rows[-1]])
    def test_lock_equality(self):
        self.assertTrue(latch(D(9600),D(10000)));self.assertTrue(D(9900)<=D('.99')*D(10000))
    def test_hold_flat(self):
        r=evaluate(self.fixture(),'hold',D('.008'),D(0));self.assertTrue(r['hold_built']);self.assertEqual(r['buy_fills'],4)

    def test_hold_no_rebuy_and_sticky_lock(self):
        rows=self.fixture()
        for i in range(70,204): rows[i][1:5]=['50','50','50','50']
        r=evaluate(rows,'hold',D('.008'),D(0))
        self.assertTrue(r['locked']);self.assertEqual(D(r['btc']),0);self.assertEqual(r['buy_fills'],4)
    def test_reconcile_and_invalid_ohlc(self):
        r=evaluate(self.fixture(),'hold',D('.01'),D('.001'))
        self.assertEqual(D(r['final_nav']),D(r['cash'])+D(r['btc'])*100-D(r['exit_reserve']))
        rows=self.fixture();rows[-1][2]='90'
        with self.assertRaises(ValueError):validate(rows)

if __name__=='__main__':
    if sys.argv[1:] == ['test']:unittest.main(argv=[sys.argv[0]])
    else:
        rows=json.loads(Path(sys.argv[1]).read_text())
        results={k:[evaluate(rows,p,f,s) for p in ('sma50','hold','cash')] for k,f,s in [('base',D('.008'),D(0)),('stress',D('.01'),D('.001'))]}
        print(json.dumps(dict(model='daily-bar-proxy-v1',start='2026-06-25T00:00:00Z',end_exclusive='2026-11-16T00:00:00Z',days=144,results=results),indent=2))
