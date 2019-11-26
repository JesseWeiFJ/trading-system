from jtrader.broker.gateway.websocket_api import TradeWebsocketApi
from jtrader.datatype import *
from jtrader.core.common import logger

import datetime
import time
import websocket

from jtrader.core.tools import BusyScheduler, DelayJob, ExceptionCatchFunctor


class FCoinTradeStream(TradeWebsocketApi):

    def __init__(self, api):
        super(FCoinTradeStream, self).__init__(api)
        self._scheduler = BusyScheduler()
        func = ExceptionCatchFunctor(self._run_user_stream, cancel_on_exception=False)
        self._scheduler.add_job(DelayJob('10s', func))

    def subscribe_user_stream(self):
        pass

    def start(self):
        self._scheduler.start()

    def stop(self):
        self._scheduler.stop()

    def _run_user_stream(self):
        for order in iter(self.api.oms):
            if order.order_id and order.status == EnumOrderStatus.PENDING:
                order_status = self.api.fetch_order_status(order)
                order.on_order(order_status)
                if order.is_closed():
                    self.api.on_order(order)

        self.api.oms.purge()
