import json
import importlib.metadata as metadata
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.config import BacktestEngineConfig, LoggingConfig
from nautilus_trader.model.data import QuoteTick
from nautilus_trader.model.enums import AccountType, OmsType, OrderSide
from nautilus_trader.model.objects import Money
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.trading.strategy import Strategy

def run(case):
    instrument=TestInstrumentProvider.btcusdt_binance()
    venue=instrument.id.venue
    engine=BacktestEngine(BacktestEngineConfig(logging=LoggingConfig(bypass_logging=True)))
    engine.add_venue(venue=venue, oms_type=OmsType.NETTING, account_type=AccountType.CASH,
                     starting_balances=[Money(10000,instrument.quote_currency)])
    engine.add_instrument(instrument)
    origin=1736175600000000000
    minute=60_000_000_000
    asks=[101,100 if case=="touch" else 99,101]
    events=[origin,origin if case=="stale_late" else origin+minute,origin+2*minute]
    if case=="stale_equal":
        asks=[99,101,101]
    ticks=[QuoteTick(instrument.id,instrument.make_price(ask-.5),instrument.make_price(ask),
                     instrument.make_qty(1000),instrument.make_qty(1000),event,origin+i*minute)
           for i,(ask,event) in enumerate(zip(asks,events))]
    observed=[]
    class Buy(Strategy):
        def on_start(self):
            self.subscribe_quote_ticks(instrument.id)
        def on_quote_tick(self,tick):
            observed.append({"event":tick.ts_event,"receive":tick.ts_init,"ask":str(tick.ask_price)})
            if len(observed)==1:
                self.submit_order(self.order_factory.limit(instrument.id,OrderSide.BUY,
                                                           instrument.make_qty(2),instrument.make_price(100)))
    engine.add_strategy(Buy())
    engine.add_data(ticks)
    engine.run()
    orders=engine.trader.generate_order_fills_report()
    all_orders=engine.trader.generate_orders_report()
    account=engine.trader.generate_account_report(venue)
    output={"case":case,"observed":observed,"orders":len(all_orders),
            "fills":orders.to_dict(orient="records"),"account_tail":account.tail(1).to_dict(orient="records")}
    assert len(all_orders)==1
    if case=="cross":
        assert len(orders)>0, output
    engine.dispose()
    return output

print(json.dumps({"engine":"nautilus_trader","version":metadata.version("nautilus_trader"),
                  "cases":[run(x) for x in ["touch","cross","stale_equal","stale_late"]],
                  "scope":"BacktestEngine quote data, Strategy, OMS, matching, generated fills and account report; published stable 1.x, not the source snapshot 2.x."},default=str))
