#!/usr/bin/env python
# -*- coding: utf-8 -*-
from jtrader.trader.algo.algorithm import AlgorithmTemplate

from jtrader.datatype import *


class StopOrderAlgorithm(AlgorithmTemplate):
    TAG = EnumOrderType.STOP

    def __init__(self, order: OrderData):
        super(StopOrderAlgorithm, self).__init__(order)
        param_dict = order.parameter
        self.price_level = param_dict.get('price_level', 0)
        self._sent = False
        self._depth: DepthData = None

    def _best_price(self):
        direction = self.target_order.direction
        if direction == EnumOrderDirection.BUY:
            price = self._depth.bid_prices[self.price_level]
        else:
            price = self._depth.ask_prices[self.price_level]
        return price

    def on_depth(self, depth: DepthData):
        super(StopOrderAlgorithm, self).on_depth(depth)
        self._depth = depth
        if not self._sent:

            volume = self.target_order.volume
            direction = self.target_order.direction
            order_price = self.target_order.price
            price = self._best_price()

            long_triggered = direction == EnumOrderDirection.BUY and price >= order_price
            short_triggered = direction == EnumOrderDirection.SELL and price <= order_price

            if long_triggered or short_triggered:
                self.create_order(self.target_order.symbol, price, volume, direction, EnumOrderType.LIMIT)
                self._sent = True

    def on_order_status(self, order: OrderData):
        super(StopOrderAlgorithm, self).on_order_status(order)
        if order.is_closed():
            self.target_order.status = order.status
            self.on_stop()
