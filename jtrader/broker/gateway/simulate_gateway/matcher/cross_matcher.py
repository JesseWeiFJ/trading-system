#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jtrader.broker.gateway.simulate_gateway.matcher.matcher import Matcher
from jtrader.datatype import *
from jtrader.core.common import logger

from collections import defaultdict, OrderedDict
import typing


class OrderContainer(object):

    def __init__(self):
        self._order_dict: typing.Dict[str, OrderData] = OrderedDict()
        self._count = 0

    def add(self, order: OrderData):
        if order.client_order_id not in self._order_dict:
            self._count += 1
            self._order_dict[order.client_order_id] = order
            logger.debug('order %s created in matcher', order.client_order_id)

    def remove_by_id(self, client_order_id):
        if client_order_id in self._order_dict:
            self._count -= 1
            self._order_dict.pop(client_order_id)

    def is_empty(self):
        return self._count == 0

    def __iter__(self):
        return iter(self._order_dict.values())


class CrossMatcher(Matcher):

    TAG = 'cross'

    def __init__(self):
        super(CrossMatcher, self).__init__()
        self._order_container_dict: typing.Dict[str, OrderContainer] = defaultdict(OrderContainer)

    def _match_order(self, order: OrderData, buy_cross_price, sell_cross_price, buy_best_price, sell_best_price):
        direction = order.direction
        buy_cross = (direction == EnumOrderDirection.BUY and
                     order.price >= buy_cross_price)

        sell_cross = (direction == EnumOrderDirection.SELL and
                      order.price <= sell_cross_price)

        if buy_cross or sell_cross or order.order_type == EnumOrderType.MARKET:
            order.status = EnumOrderStatus.FILLED
            order.executed_volume = order.volume
            order.order_id = generate_id()

            trade = TradeData.from_order(order)
            trade.trade_id = generate_id()

            if direction == EnumOrderDirection.BUY:
                trade.price = min(order.price, buy_best_price)
            else:
                trade.price = max(order.price, sell_best_price)

            trade.commission = trade.price * trade.volume * self.fee_rate
            trade.commission_asset = trade.contract.asset_quote

            logger.debug('trade matched\n%s', trade.pretty_string())
            self.callback(trade)
            self.callback(order)
            return order.client_order_id
        return ''

    def on_bar(self, bar: BarData):
        container = self._order_container_dict[bar.symbol]
        if not container.is_empty():
            buy_cross_price = bar.low  # 若买入方向限价单价格高于该价格，则会成交
            sell_cross_price = bar.high  # 若卖出方向限价单价格低于该价格，则会成交
            buy_best_price = bar.open  # 在当前时间点前发出的买入委托可能的最优成交价
            sell_best_price = bar.open  # 在当前时间点前发出的卖出委托可能的最优成交价
            matcher_ids = []
            for order in iter(container):
                match_id = self._match_order(order, buy_cross_price, sell_cross_price, buy_best_price, sell_best_price)
                if match_id:
                    matcher_ids.append(match_id)
            for match_id in matcher_ids:
                container.remove_by_id(match_id)

    def on_depth(self, depth: DepthData):
        container = self._order_container_dict[depth.symbol]
        if not container.is_empty():
            buy_cross_price = depth.ask_prices[0]
            sell_cross_price = depth.bid_prices[0]
            buy_best_price = depth.ask_prices[0]
            sell_best_price = depth.bid_prices[0]
            matcher_ids = []
            for order in container:
                match_id = self._match_order(order, buy_cross_price, sell_cross_price, buy_best_price, sell_best_price)
                if match_id:
                    matcher_ids.append(match_id)
            for match_id in matcher_ids:
                container.remove_by_id(match_id)

    def match_order(self, order: OrderData):
        if EnumOrderStatus.NEW == order.status:
            self._order_container_dict[order.symbol].add(order)
            order.status = EnumOrderStatus.PENDING
            order.order_id = generate_id()
            self.callback(order)

        elif EnumOrderStatus.CANCELLING == order.status:
            self._order_container_dict[order.symbol].remove_by_id(order.client_order_id)
            order.status = EnumOrderStatus.CANCELLED
            self.callback(order)
            logger.debug('order %s cancelled', order.client_order_id)

