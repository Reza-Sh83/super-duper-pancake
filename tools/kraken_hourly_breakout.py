"""Fixture-only implementation of Architect's frozen Kraken hourly bar proxy."""

import argparse
from dataclasses import dataclass, field
from decimal import Decimal, localcontext
import json

from crypto_paper.data import dump, parse_time, stamp, NANO

D = Decimal
HOUR = 3600
DAY = 24 * HOUR
START = parse_time("2026-11-23T00:00:00Z") // NANO
END = parse_time("2026-12-14T00:00:00Z") // NANO
NOT_BEFORE = "2026-12-15T00:00:00Z"
ENDPOINT = "https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=60"
INITIAL = D(10000)
WARMUP = 26
WINDOW_HOURS = 504
COSTS = {"base": (D(".008"), D(0)), "stress": (D(".01"), D(".001"))}
HOLD_BUDGETS = {"hold_2_5_percent": INITIAL * D(".025"), "hold_full": INITIAL}


class BlockedInput(ValueError):
    """The fixed window cannot be evaluated from the supplied rows."""


@dataclass(frozen=True)
class Bar:
    utc: int
    opening: Decimal
    high: Decimal
    low: Decimal
    close: Decimal


def fixed_bars(rows):
    """Validate ordered Kraken-style rows for the fixed evaluation plus warm-up."""
    wanted = range(START - WARMUP * HOUR, END, HOUR)
    bars = []
    previous = None
    for row in rows:
        try:
            utc = row[0]
            if type(utc) is not int or utc % HOUR or (previous is not None and utc <= previous):
                raise BlockedInput("duplicate, unordered or off-grid hourly row")
            previous = utc
            if utc not in wanted:
                continue
            if any(type(value) not in (int, str, Decimal) for value in row[1:5]):
                raise BlockedInput("OHLC must use exact decimal input")
            o, high, low, close = map(D, row[1:5])
            if (not all(value.is_finite() and value > 0 for value in (o, high, low, close))
                    or not low <= min(o, close) <= max(o, close) <= high):
                raise BlockedInput("nonpositive, nonfinite or inconsistent OHLC")
        except (ArithmeticError, IndexError, KeyError, TypeError) as error:
            raise BlockedInput("malformed hourly row") from error
        bars.append(Bar(utc, o, high, low, close))
    if [bar.utc for bar in bars] != list(wanted):
        raise BlockedInput("missing evaluation or warm-up hours")
    return bars


def kraken_closed_rows(response):
    """Parse a retained response, strictly excluding its last uncommitted row."""
    try:
        data = json.loads(response, parse_float=D)
        if data["error"] != []:
            raise BlockedInput("Kraken reported an API error")
        pairs = set(data["result"]) - {"last"}
        if pairs != {"XXBTZUSD"}:
            raise BlockedInput("unexpected Kraken pair")
        rows = data["result"]["XXBTZUSD"]
        if not isinstance(rows, list) or len(rows) < 2:
            raise BlockedInput("insufficient closed Kraken rows")
        return rows[:-1]
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise BlockedInput("malformed Kraken response") from error


def signals(bars, index):
    close = bars[index-2].close
    high = max(bar.high for bar in bars[index-26:index-2])
    low = min(bar.low for bar in bars[index-14:index-2])
    return close > high, close < low


@dataclass
class Account:
    fee: Decimal
    slip: Decimal
    cash: Decimal = INITIAL
    btc: Decimal = D(0)
    paid_fees: Decimal = D(0)
    turnover: Decimal = D(0)
    peak: Decimal = INITIAL
    drawdown: Decimal = D(0)
    exposure: Decimal = D(0)
    exposure_total: Decimal = D(0)
    exposure_samples: int = 0
    day_open: Decimal = INITIAL
    locks: dict = field(default_factory=dict)
    fills: list = field(default_factory=list)
    days: list = field(default_factory=list)

    def liquidation_unit(self, price):
        return price * (1 - self.slip) * (1 - self.fee)

    def nav(self, price):
        return self.cash + self.btc * self.liquidation_unit(price)

    def observe(self, price, utc, phase, enforce_risk=False):
        nav = self.nav(price)
        self.peak = max(self.peak, nav)
        self.drawdown = max(self.drawdown, 100 * (self.peak - nav) / self.peak)
        exposure = 100 * self.btc * price / nav
        self.exposure = max(self.exposure, exposure)
        self.exposure_total += exposure
        self.exposure_samples += 1
        if enforce_risk:
            if nav <= self.day_open * D(".99"):
                self.locks.setdefault("daily_loss", {"utc": utc, "phase": phase})
            if nav <= self.peak * D(".96"):
                self.locks.setdefault("drawdown", {"utc": utc, "phase": phase})
        return nav

    def fill(self, side, quantity, price, utc, reason, limit=None):
        if quantity <= 0:
            return
        buy = side == "buy"
        execution = price * (1 + self.slip if buy else 1 - self.slip)
        gross = quantity * execution
        fee = gross * self.fee
        if buy:
            available = self.cash if limit is None else min(self.cash, limit)
            # Decimal division can round a boundary quantity up by one ULP.
            while gross + fee > available:
                quantity = quantity.next_minus()
                gross = quantity * execution
                fee = gross * self.fee
            self.cash -= gross + fee
            self.btc += quantity
        else:
            if quantity > self.btc:
                raise ValueError("cannot short")
            self.cash += gross - fee
            self.btc -= quantity
        self.turnover += gross
        self.paid_fees += fee
        self.fills.append({"utc": utc, "side": side, "qty_btc": quantity,
                           "execution_usd": execution, "gross_usd": gross, "fee_usd": fee,
                           "reason": reason})

    def enter(self, price, utc):
        nav = self.nav(price)
        unit = price * (1 + self.slip) * (1 + self.fee)
        mark = self.liquidation_unit(price)
        cap_cost = unit + D(".10") * (unit - mark)
        quantity = min(self.cash/unit, D(".025")*nav/unit, D(".10")*nav/cap_cost)
        self.fill("buy", quantity, price, utc, "breakout", D(".025") * nav)

    def act(self, price, utc, active_signals):
        enter, leave = active_signals
        if self.locks:
            self.fill("sell", self.btc, price, utc, "risk_lock")
        elif self.btc:
            if leave:
                self.fill("sell", self.btc, price, utc, "range_exit")
            else:
                # Selling at the net opening liquidation mark preserves NAV.
                excess = self.btc - D(".10") * self.nav(price) / price
                self.fill("sell", excess, price, utc, "exposure_trim")
        elif enter:
            self.enter(price, utc)

    def summary(self, final_close):
        nav = self.nav(final_close)
        fee_reserve = self.btc * final_close * (1 - self.slip) * self.fee
        slippage_reserve = self.btc * final_close * self.slip
        returns = [row["net_percent"] for row in self.days]
        return {"initial_usd": INITIAL, "cash_usd": self.cash, "btc": self.btc,
                "nav_usd": nav, "net_usd": nav - INITIAL, "net_percent": 100 * (nav/INITIAL - 1),
                "fees_usd": self.paid_fees, "turnover_usd": self.turnover, "fills": self.fills,
                "exit_fee_reserve_usd": fee_reserve,
                "exit_slippage_reserve_usd": slippage_reserve,
                "total_exit_reserve_usd": fee_reserve + slippage_reserve,
                "sampled_drawdown_percent": self.drawdown,
                "mean_sampled_gross_exposure_percent": self.exposure_total / self.exposure_samples,
                "max_sampled_gross_exposure_percent": self.exposure, "locks": self.locks,
                "daily_outcomes": self.days, "daily_returns_sorted_percent": sorted(returns),
                "best_day": max(self.days, key=lambda row: row["net_percent"]),
                "worst_day": min(self.days, key=lambda row: row["net_percent"]),
                "days_at_least_50_percent": sum(value >= 50 for value in returns)}


def evaluate_fixture(rows):
    """Evaluate the frozen model using only caller-supplied synthetic fixture rows."""
    with localcontext() as ctx:
        ctx.prec = 34
        bars = fixed_bars(rows)
        results = {}
        for scenario, (fee, slip) in COSTS.items():
            arms = {name: Account(fee, slip) for name in ("breakout", "cash", *HOLD_BUDGETS)}
            for index in range(WARMUP, len(bars)):
                bar = bars[index]
                signal = signals(bars, index)
                for name, account in arms.items():
                    strategy = name == "breakout"
                    if bar.utc % DAY == 0:
                        account.day_open = account.nav(bar.opening)
                    account.observe(bar.opening, bar.utc, "pre_open", strategy)
                    if strategy:
                        account.act(bar.opening, bar.utc, signal)
                    elif index == WARMUP and name in HOLD_BUDGETS:
                        budget = HOLD_BUDGETS[name]
                        unit = bar.opening * (1 + slip) * (1 + fee)
                        account.fill("buy", budget/unit, bar.opening, bar.utc, "hold_entry", budget)
                    account.observe(bar.opening, bar.utc, "post_open", strategy)
                    cutoff = bar.utc + HOUR
                    close = account.observe(bar.close, cutoff, "close", strategy)
                    if cutoff % DAY == 0:
                        account.days.append({"start": bar.utc // DAY * DAY, "end_exclusive": cutoff,
                                             "opening_nav_usd": account.day_open,
                                             "closing_nav_usd": close,
                                             "net_usd": close-account.day_open,
                                             "net_percent": 100*(close/account.day_open - 1)})
            results[scenario] = {name: account.summary(bars[-1].close) for name, account in arms.items()}
        stress = results["stress"]
        return {"scope": "SYNTHETIC_FIXTURE_ONLY", "start": stamp(START*NANO),
                "end_exclusive": stamp(END*NANO), "coverage": {"hours": WINDOW_HOURS,
                "warmup_hours": WARMUP, "complete_utc_days": WINDOW_HOURS//24},
                "primary_stress_excess_percentage_points":
                    stress["breakout"]["net_percent"] - stress["hold_2_5_percent"]["net_percent"],
                "arms": results}


def synthetic_rows():
    rows = [[utc, "100", "101", "99", "100"] for utc in range(START-WARMUP*HOUR, END, HOUR)]
    rows[WARMUP-2][1:5] = ["100", "103", "99", "102"]
    rows[WARMUP][1:5] = ["100", "101", "97", "98"]
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic", action="store_true", required=True)
    parser.parse_args()
    print(dump(evaluate_fixture(synthetic_rows())))


if __name__ == "__main__":
    main()
