#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jtrader.api import CcxtApi
from jtrader.broker.gateway.gateway import Gateway
from jtrader.broker.gateway.websocket_api import MarketWebsocketApi, TradeWebsocketApi, AggregateWebsocketApi
from jtrader.datatype import *


class CcxtGateway(Gateway):
    TAG = ''

    def __init__(self):
        super(CcxtGateway, self).__init__()
        self.rest_api: CcxtApi = None
        self.market_ws_api: MarketWebsocketApi = None
        self.trade_ws_api: TradeWebsocketApi = None
        self.agg_ws_api: AggregateWebsocketApi = None

    def configure(self, gateway_config: dict = None):
        api_key = gateway_config['api_key']
        api_secret = gateway_config['api_secret']

        symbol_list = gateway_config['symbol']
        frequency_list = gateway_config['frequency']
        depth_flag = gateway_config.get('depth_flag', True)

        self.rest_api.set_callback(self.callback)
        self.rest_api.connect(api_key, api_secret)
        if symbol_list:
            if self.agg_ws_api is not None:
                self.agg_ws_api.init(symbol_list, frequency_list, depth_flag)
            else:
                self.market_ws_api.init(symbol_list, frequency_list, depth_flag)
        if not api_key:
            self.trade_ws_api = None

    def send_order(self, order: OrderData):
        if order.status == EnumOrderStatus.NEW:
            self.rest_api.create_order(order)
        elif order.status == EnumOrderStatus.CANCELLING:
            self.rest_api.cancel_order(order)
        else:
            raise TypeError(f'Order to send has no corresponding action: {order}')

    def cancel_all(self):
        for order in self.rest_api.oms:
            if not order.is_closed():
                order.status = EnumOrderStatus.CANCELLING
                self.rest_api.cancel_order(order)

    def query_balance(self, currency=None):
        return self.rest_api.fetch_balance()

    def start(self):
        super(CcxtGateway, self).start()
        if self.agg_ws_api:
            self.agg_ws_api.start()
        if self.market_ws_api:
            self.market_ws_api.start()
        if self.trade_ws_api:
            self.trade_ws_api.start()

    def stop(self):
        super(CcxtGateway, self).stop()
        if self.agg_ws_api:
            self.agg_ws_api.stop()
        if self.market_ws_api:
            self.market_ws_api.stop()
        if self.trade_ws_api:
            self.trade_ws_api.stop()
