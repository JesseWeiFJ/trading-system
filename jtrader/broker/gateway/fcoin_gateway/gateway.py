from jtrader.broker.gateway.ccxt_gateway import CcxtGateway
from jtrader.datatype import ExchangeAbbr
from jtrader.api import FCoinApi
from .market_stream import FCoinMarketStream
from .trade_stream import FCoinTradeStream


class FCoinGateway(CcxtGateway):
    TAG = ExchangeAbbr.FCOIN

    def __init__(self):
        super(FCoinGateway, self).__init__()
        self.rest_api = FCoinApi()
        self.trade_ws_api = FCoinTradeStream(self.rest_api)
        self.market_ws_api = FCoinMarketStream(self.rest_api)
