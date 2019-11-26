from jtrader.broker.gateway.ccxt_gateway import CcxtGateway
from jtrader.datatype import ExchangeAbbr
from .stream import BitmexStream
from jtrader.api import BitmexApi


class BitmexGateway(CcxtGateway):
    TAG = ExchangeAbbr.BITMEX

    def __init__(self):
        super(BitmexGateway, self).__init__()
        self.rest_api = BitmexApi()
        self.agg_ws_api = BitmexStream(self.rest_api)
