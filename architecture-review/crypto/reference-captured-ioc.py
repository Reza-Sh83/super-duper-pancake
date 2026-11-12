from decimal import Decimal as D
import json,sys
p=json.load(sys.stdin)
snap, update = p["raw"][:2]
d=json.loads(snap["wire"],parse_float=D)["data"][0]
levels=sorted([(D(x["price"]),D(x["qty"])) for x in d["asks"]])
age=p["checks"][0]["apparentAgeMs"]
limit=levels[0][0]
def ioc(fresh, limit, quantity):
    if not fresh:
        return D(0),D(0),D(0)
    filled=notional=D(0)
    for price, size in levels:
        if price>limit or filled==quantity:
            break
        take=min(size,quantity-filled)
        filled+=take
        notional+=take*price
    return filled,notional,notional*D("0.001")
n=levels[0][1]+D("0.01")
assert ioc(age<=5000,limit,n)==(0,0,0)
filled,notional,fee=ioc(True,limit,n)
assert filled==levels[0][1] and n-filled==D("0.01") and fee>0
assert ioc(True,limit-D("0.01"),n)==(0,0,0)
print(json.dumps(dict(classification="offline reference on captured Kraken snapshot, synthetic freshness positive control and hypothetical fee; no venue orders or candidate engine",age_ms=age,fixture_cap_ms=5000,stale_fill="0",ioc_filled=str(filled),ioc_cancelled=str(n-filled),notional=str(notional),fee=str(fee),limit=str(limit),assertions=3)))
