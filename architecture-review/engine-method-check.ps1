$cs=@'
using System;
enum OrderStatus { Submitted,Canceled,Filled }
enum OrderDirection { Buy,Sell }
class Order { public OrderStatus Status=OrderStatus.Submitted; public OrderDirection Direction=OrderDirection.Buy; public DateTime Time; }
class OrderFee { public static readonly OrderFee Zero=new OrderFee(); }
class OrderEvent { public OrderStatus Status=OrderStatus.Submitted; public decimal FillPrice,FillQuantity; public OrderEvent(Order o,DateTime t,OrderFee f){} }
class Exchange { public TimeZoneInfo TimeZone=TimeZoneInfo.Utc; }
class Security { public DateTime LocalTime=DateTime.UnixEpoch; public Exchange Exchange=new Exchange(); }
class Prices { public decimal Low,High; public DateTime EndTime; }
static class Clock { public static DateTime ConvertToUtc(this DateTime d,TimeZoneInfo tz){return d;} }
public class LeanFixture {
 private Prices prices;
 private bool IsExchangeOpen(Security a){return true;}
 private Prices GetPricesCheckingPythonWrapper(Security a,OrderDirection d){return prices;}
        private OrderEvent InternalLimitFill(Security asset, Order order, decimal limitPrice, decimal quantity)
        {
            //Initialise;
            var utcTime = asset.LocalTime.ConvertToUtc(asset.Exchange.TimeZone);
            var fill = new OrderEvent(order, utcTime, OrderFee.Zero);

            //If its cancelled don't need anymore checks:
            if (order.Status == OrderStatus.Canceled) return fill;

            // make sure the exchange is open before filling -- allow pre/post market fills to occur
            if (!IsExchangeOpen(asset))
            {
                return fill;
            }
            //Get the range of prices in the last bar:
            var orderDirection = order.Direction;
            var prices = GetPricesCheckingPythonWrapper(asset, orderDirection);
            var pricesEndTime = prices.EndTime.ConvertToUtc(asset.Exchange.TimeZone);

            // do not fill on stale data
            if (pricesEndTime <= order.Time) return fill;

            //-> Valid Live/Model Order:
            switch (orderDirection)
            {
                case OrderDirection.Buy:
                    //Buy limit seeks lowest price
                    if (prices.Low < limitPrice)
                    {
                        //Set order fill:
                        fill.Status = OrderStatus.Filled;
                        // fill at the worse price this bar or the limit price, this allows far out of the money limits
                        // to be executed properly
                        fill.FillPrice = Math.Min(prices.High, limitPrice);
                        // assume the order completely filled
                        fill.FillQuantity = quantity;
                    }
                    break;
                case OrderDirection.Sell:
                    //Sell limit seeks highest price possible
                    if (prices.High > limitPrice)
                    {
                        fill.Status = OrderStatus.Filled;
                        // fill at the worse price this bar or the limit price, this allows far out of the money limits
                        // to be executed properly
                        fill.FillPrice = Math.Max(prices.Low, limitPrice);
                        // assume the order completely filled
                        fill.FillQuantity = quantity;
                    }
                    break;
            }

            return fill;
        }
 public static string Run(decimal high,decimal low,bool stale){
  var time=DateTime.UnixEpoch;
  var model=new LeanFixture{prices=new Prices{High=high,Low=low,EndTime=stale?time:time.AddMinutes(1)}};
  var f=model.InternalLimitFill(new Security(),new Order{Time=time},100m,2m);
  return f.Status==OrderStatus.Filled?f.FillPrice.ToString()+"/"+f.FillQuantity.ToString():"none";
 }
}
'@
Add-Type -TypeDefinition $cs -ErrorAction Stop
$lean=@([LeanFixture]::Run(101,100,$false),[LeanFixture]::Run(101,99,$false),[LeanFixture]::Run(102,101,$false),[LeanFixture]::Run(101,99,$true)); if(($lean -join ',') -ne 'none,100/2,none,none'){throw ('Unexpected LEAN: '+($lean -join ','))}; $py=@'
from types import SimpleNamespace as S
from enum import Enum
import json
class OrderSide(Enum):
    BUY=1
    SELL=2
class ConditionalOrderMode(Enum):
    EXECUTION_PRICE=1
class Model:
    def check_limit_fill(
        self, order, high: float, low: float, price: float | None = None
    ) -> float | None:
        if order.limit_price is None:
            return None
        if self.broker.conditional_order_mode is ConditionalOrderMode.EXECUTION_PRICE:
            if price is not None and (
                order.side is OrderSide.BUY
                and price <= order.limit_price
                or order.side is OrderSide.SELL
                and price >= order.limit_price
            ):
                return price
            return None
        if (
            order.side == OrderSide.BUY
            and low <= order.limit_price
            or order.side == OrderSide.SELL
            and high >= order.limit_price
        ):
            return order.limit_price
        return None
model=Model()
model.broker=S(conditional_order_mode=None)
order=S(limit_price=100,side=OrderSide.BUY)
out=[model.check_limit_fill(order,h,l) for h,l in [(101,100),(101,99),(102,101),(101,99)]]
assert out == [100,100,None,100]
print(json.dumps(out))
'@
$result=$py | python -; if($LASTEXITCODE){exit $LASTEXITCODE}; @{lean=$lean;ml4t=($result | ConvertFrom-Json);cases=@('touch','cross','unreached','stale_cross');runtime=@($PSVersionTable.PSVersion.ToString(),(python --version))} | ConvertTo-Json -Compress
