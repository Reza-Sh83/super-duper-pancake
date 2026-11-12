import importlib.metadata as metadata
import json
from datetime import UTC, datetime, timedelta

import polars as pl
from ml4t.backtest import BacktestConfig, DataFeed, Engine, Strategy
from ml4t.backtest.config import ExecutionMode
from ml4t.backtest.types import OrderType

def ml4t_case(case):
    origin = datetime(2025, 1, 6, 15, tzinfo=UTC)
    times = [origin + timedelta(minutes=i) for i in range(3)]
    lows = [99, 101, 101] if case == "stale_equal" else [101, 100 if case == "touch" else 99, 101]
    frame = pl.DataFrame({"timestamp": times, "asset": ["TEST"] * 3,
        "open": [102.0] * 3, "high": [103.0] * 3, "low": list(map(float, lows)),
        "close": [102.0] * 3, "volume": [1000.0] * 3})
    orders = []
    class Buy(Strategy):
        def on_data(self, timestamp, data, context, broker):
            if timestamp == times[0]:
                orders.append(broker.submit_order("TEST", 2, order_type=OrderType.LIMIT, limit_price=100))
    result = Engine(DataFeed(prices_df=frame), Buy(),
                    BacktestConfig(calendar=None, initial_cash=10000, execution_mode=ExecutionMode.NEXT_BAR)).run()
    fills = result.to_fills_dataframe()
    assert len(orders) == 1
    assert fills.height == (0 if case == "stale_equal" else 1), (case, fills)
    if fills.height:
        assert fills["timestamp"].to_list() == [times[1]]
        assert fills["quantity"].to_list() == [2.0]
        assert fills["price"][0] <= 100
    portfolio = result.to_portfolio_state_dataframe()
    return {"case": case, "submitted": str(orders[0].status), "fills": fills.to_dicts(), "final_cash": portfolio["cash"][-1]}

if __name__ == "__main__":
    print(json.dumps({"engine": "ml4t-backtest", "version": metadata.version("ml4t-backtest"),
                      "cases": [ml4t_case(case) for case in ["touch", "cross", "stale_equal"]],
                      "scope": "Actual Engine DataFeed, strategy, submit, matching, fills and cash. Stale_equal tests submission bar reuse. Event-vs-receive split not supported in this bar fixture."}, default=str))
