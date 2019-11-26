from jtrader.broker.gateway.ccxt_gateway import CcxtGateway
from jtrader.datatype import ExchangeAbbr
from jtrader.api import BinanceApi
from .stream import BinanceStream


class BinanceGateway(CcxtGateway):
    TAG = ExchangeAbbr.BINANCE

    def __init__(self):
        super(BinanceGateway, self).__init__()
        self.rest_api = BinanceApi()
        self.agg_ws_api = BinanceStream(self.rest_api)
