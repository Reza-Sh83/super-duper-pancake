import json, hashlib, urllib.request, time
from decimal import Decimal as D, ROUND_FLOOR
from datetime import datetime, timezone
def get(path):
    t=time.time_ns()
    with urllib.request.urlopen("https://api.kraken.com/0/public/"+path,timeout=10) as r:
        raw=r.read()
    obj=json.loads(raw)
    assert not obj["error"]
    return obj["result"],hashlib.sha256(raw).hexdigest(),t
bars={}
for interval in (240,1440):
    response,h,t=get("OHLC?pair=XBTUSD&interval="+str(interval))
    rows=next(v for k,v in response.items() if k!="last")
    ts=[r[0] for r in rows[:-1]]
    assert len(ts)>=50 and ts==sorted(set(ts))
    assert all(x%(60*interval)==0 for x in ts)
    assert rows[-1][0]==ts[-1]+60*interval
    assert all(len(r)==8 and D(r[3])<=min(D(r[1]),D(r[4]))<=max(D(r[1]),D(r[4]))<=D(r[2]) for r in rows[:-1])
    bars[str(interval)]={"closed_rows":len(ts),"last_closed_start":ts[-1],"excluded_open_start":rows[-1][0],"sha256":h}
pairs,ph,_=get("AssetPairs?pair=XBTUSD")
p=next(iter(pairs.values()))
depth,bh,_=get("Depth?pair=XBTUSD&count=5")
b=next(iter(depth.values()))
ask,avail=map(D,b["asks"][0][:2]); tick=D(str(p["tick_size"]))
step=D(10)**-p["lot_decimals"]; fee=D(".008"); cash=D(10000)
limit=(ask*D("1.002")/tick).to_integral_value(rounding=ROUND_FLOOR)*tick
qty=(D(250)/(limit*(1+fee))/step).to_integral_value(rounding=ROUND_FLOOR)*step
assert qty>=D(p["ordermin"]) and qty*ask>=D(p["costmin"]) and qty*limit*(1+fee)<=250
filled=min(qty,avail); assert filled>0
cost=filled*ask; commission=cost*fee; cash-=cost+commission
assert cash+cost+commission==D(10000)
print(json.dumps(dict(bars=bars,metadata={k:p.get(k) for k in ("tick_size","lot_decimals","ordermin","costmin","status")},metadata_hash=ph,depth_hash=bh,reference_snapshot_only={"qty":str(qty),"first_level_fill":str(filled),"price":str(ask),"fee":str(commission),"cash_after_first_fill":str(cash)},scope="Live unauthenticated REST plus isolated arithmetic; not the implemented WS paper path or holdout.")))
