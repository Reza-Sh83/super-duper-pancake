import json
from decimal import Decimal as D, ROUND_FLOOR
from datetime import datetime as T
x=json.loads("{\"schema_version\":1,\"utc\":{\"bar_start\":\"2026-01-01T00:00:00Z\",\"bar_end\":\"2026-01-01T04:00:00Z\",\"accept\":[\"2026-01-01T04:00:02Z\",\"2026-01-01T04:01:00Z\"],\"reject\":\"2026-01-01T04:01:00.001Z\",\"open_row_start\":\"2026-01-01T04:00:00Z\",\"repeat_intents\":0},\"ioc\":{\"cash\":\"10000\",\"ask_levels\":[[\"100\",\"1\"],[\"100.1\",\"0.5\"],[\"100.3\",\"10\"]],\"bid\":\"99.9\",\"price_tick\":\"0.1\",\"qty_step\":\"0.01\",\"qty_min\":\"0.01\",\"cost_min\":\"0.5\",\"fee\":\"0.008\",\"limit\":\"100.2\",\"requested\":\"2.47\",\"expected\":{\"filled\":\"1.5\",\"cancelled\":\"0.97\",\"gross\":\"150.05\",\"fee\":\"1.2004\",\"cash\":\"9848.7496\",\"nav\":\"9997.4008\"},\"partial_exit\":{\"qty\":\"0.4\",\"price\":\"99.9\",\"fee\":\"0.31968\",\"cash\":\"9888.38992\",\"btc\":\"1.1\",\"nav\":\"9997.4008\"}}}")
u=x["utc"]; start=T.fromisoformat(u["bar_start"]); end=T.fromisoformat(u["bar_end"])
assert (end-start).total_seconds()==14400 and T.fromisoformat(u["open_row_start"])==end
assert all(2<=(T.fromisoformat(v)-end).total_seconds()<=60 for v in u["accept"])
assert (T.fromisoformat(u["reject"])-end).total_seconds()>60
s=x["ioc"]; f=D(s["fee"]); tick=D(s["qty_step"]); limit=D(s["limit"])
q=(D(250)/(limit*(1+f))/tick).to_integral_value(rounding=ROUND_FLOOR)*tick
assert q==D(s["requested"])
filled=cost=D(0)
for price,size in s["ask_levels"]:
    price,size=D(price),D(size)
    if price>limit:break
    take=min(size,q-filled)
    filled+=take
    cost+=take*price
fee=cost*f; cash=D(s["cash"])-cost-fee
nav=cash+filled*D(s["bid"])*(1-f)
for k,v in dict(filled=filled,cancelled=q-filled,gross=cost,fee=fee,cash=cash,nav=nav).items():assert v==D(s["expected"][k]),k
p=s["partial_exit"]; out=D(p["qty"]); gross=out*D(p["price"])
assert gross*f==D(p["fee"])
assert cash+gross*(1-f)==D(p["cash"])
assert filled-out==D(p["btc"])
assert D(p["cash"])+D(p["btc"])*D(s["bid"])*(1-f)==D(p["nav"])
print(json.dumps(dict(status="PASS",scope="UTC fixture and decimal arithmetic reference; no product invocation",assertion_groups=6)))
