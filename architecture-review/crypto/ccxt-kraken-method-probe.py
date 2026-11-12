import json,textwrap,hashlib,urllib.request,urllib.parse
source="    def fetch_order_book(self, symbol: str, limit: Int = None, params: dict = {}) -> OrderBook:\n        \"\"\"\n        fetches information on open orders with bid(buy) and ask(sell) prices, volumes and other data\n\n        https://docs.kraken.com/api-reference/market-data/get-order-book\n\n        :param str symbol: unified symbol of the market to fetch the order book for\n        :param int [limit]: the maximum amount of order book entries to return\n        :param dict [params]: extra parameters specific to the exchange API endpoint\n        :returns dict: an `order book structure <https://docs.ccxt.com/?id=order-book-structure>`\n        \"\"\"\n        if self.markets is None:\n            self.load_markets()\n        market = self.market(symbol)\n        request = {\n            'pair': market['id'],\n        }\n        if limit is not None:\n            request['count'] = limit  # 100\n        response = self.publicGetDepth(self.extend(request, params))\n        #\n        #     {\n        #         \"error\":[],\n        #         \"result\":{\n        #             \"XETHXXBT\":{\n        #                 \"asks\":[\n        #                     [\"0.023480\",\"4.000\",1586321307],\n        #                     [\"0.023490\",\"50.095\",1586321306],\n        #                     [\"0.023500\",\"28.535\",1586321302],\n        #                 ],\n        #                 \"bids\":[\n        #                     [\"0.023470\",\"59.580\",1586321307],\n        #                     [\"0.023460\",\"20.000\",1586321301],\n        #                     [\"0.023440\",\"67.832\",1586321306],\n        #                 ]\n        #             }\n        #         }\n        #     }\n        #\n        result = self.safe_dict(response, 'result', {})\n        orderbook = self.safe_dict(result, market['id'])\n        # sometimes kraken returns wsname instead of market id\n        # https://github.com/ccxt/ccxt/issues/8662\n        marketInfo = self.safe_dict(market, 'info', {})\n        wsName = self.safe_string(marketInfo, 'wsname')\n        if wsName is not None:\n            orderbook = self.safe_dict(result, wsName, orderbook)\n        return self.parse_order_book(orderbook, symbol)\n\n    def fetch_time(self, params: dict = {}) -> Int:\n        \"\"\"\n        fetches the current integer timestamp in milliseconds from the exchange server\n\n        https://docs.kraken.com/api-reference/market-data/get-server-time\n\n        :param dict [params]: extra parameters specific to the exchange API endpoint\n        :returns int: the current integer timestamp in milliseconds from the exchange server\n        \"\"\"\n        # https://www.kraken.com/en-us/features/api#get-server-time\n        response = self.publicGetTime(params)\n        #\n        #    {\n        #        \"error\": [],\n        #        \"result\": {\n        #            \"unixtime\": 1591502873,\n        #            \"rfc1123\": \"Sun,  7 Jun 20 04:07:53 +0000\"\n        #        }\n        #    }\n        #\n        result = self.safe_dict(response, 'result', {})\n        return self.safe_timestamp(result, 'unixtime')\n"
env=dict(Int=int,OrderBook=dict)
exec(textwrap.dedent(source),env)
class KrakenPublic:
    markets=True
    safe_dict=staticmethod(lambda d,k,default=None:d.get(k,default))
    safe_string=staticmethod(lambda d,k:d.get(k))
    safe_timestamp=staticmethod(lambda d,k:int(d[k])*1000)
    extend=staticmethod(lambda a,b:{**a,**b})
    def market(self,s): assert s=="BTC/USD"; return {"id":"XXBTZUSD","info":{"wsname":"BTC/USD"}}
    def fetch(self,path,p):
        with urllib.request.urlopen("https://api.kraken.com/0/public/"+path+"?"+urllib.parse.urlencode(p),timeout=8) as r:
            reply=json.load(r)
        assert not reply["error"],reply["error"]
        return reply
    def publicGetDepth(self,p): self.request=p;return self.fetch("Depth",p)
    def publicGetTime(self,p): return self.fetch("Time",p)
    def parse_order_book(self,book,symbol): return book
p=KrakenPublic()
book=env["fetch_order_book"](p,"BTC/USD",5)
ts=env["fetch_time"](p)
assert p.request=={"pair":"XXBTZUSD","count":5}
assert len(book["bids"])==len(book["asks"])==5
assert ts%1000==0 and ts>0
print(json.dumps(dict(pass_count=3,request=p.request,server_ms=ts,depth=5,source_sha256=hashlib.sha256(source.encode()).hexdigest(),scope="Exact CCXT Kraken method bodies, native public REST, helper and transport adapters, no full CCXT runtime or private calls")))
