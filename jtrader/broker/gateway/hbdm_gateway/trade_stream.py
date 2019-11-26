from jtrader.broker.gateway.websocket_api import TradeWebsocketApi
from jtrader.datatype import *
from jtrader.core.common import logger

import datetime
import time
import websocket

from jtrader.core.tools import BusyScheduler, DelayJob, ExceptionCatchFunctor
from jtrader.broker.gateway.hbdm_gateway.rest_api import STATUS_HBDM2VT
from jtrader.broker.gateway.hbdm_gateway.base_stream import HBDMStreamMixin


class HBDMTradeStream(HBDMStreamMixin, TradeWebsocketApi):

    HOST = "wss://api.hbdm.com/notification"

    def subscribe_user_stream(self):
        req = {
            "op": "sub",
            "cid": str(time.time()),
            "topic": f"orders.*"
        }
        self.send_packet(req)

    def on_data(self, packet):  # type: (dict)->None
        """"""
        op = packet.get("op", None)
        if op != "notify":
            return

        topic = packet["topic"]
        if "orders" in topic:
            self.on_order(packet)

    def on_order(self, data: dict):
        """"""
        dt = datetime.datetime.fromtimestamp(data["created_at"] / 1000)
        if data["client_order_id"]:
            client_order_id = data["client_order_id"]
        else:
            client_order_id = data["order_id"]

        order = self.api.oms.clone(client_order_id)
        order.order_id = data["order_id"]
        order.datetime = dt
        order.executed_volume = data["trade_volume"]
        order.executed_notional = data["trade_turnover"]
        order.status = STATUS_HBDM2VT[data["status"]]

        self.api.on_order(order)

        trades = data["trade"]
        if not trades:
            return

        for d in trades:
            dt = datetime.datetime.fromtimestamp(d["created_at"] / 1000)
            trade = TradeData.from_order(order)
            trade.trade_id = str(d["trade_id"])
            trade.datetime = dt
            trade.price = d["trade_price"]
            trade.volume = d["trade_volume"]
            self.api.on_trade(trade)

        if order.is_closed():
            self.api.oms.pop(client_order_id)

