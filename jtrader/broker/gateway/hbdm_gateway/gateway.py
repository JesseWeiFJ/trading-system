from jtrader.broker.gateway.ccxt_gateway import CcxtGateway
from jtrader.datatype import ExchangeAbbr
from .rest_api import HbdmRestApi
from .market_stream import HBDMMarketStream
from .trade_stream import HBDMTradeStream


class HBDMGateway(CcxtGateway):
    TAG = ExchangeAbbr.HBDM

    def __init__(self):
        super(HBDMGateway, self).__init__()
        self.rest_api = HbdmRestApi()
        self.trade_ws_api = HBDMTradeStream(self.rest_api)
        self.market_ws_api = HBDMMarketStream(self.rest_api)
