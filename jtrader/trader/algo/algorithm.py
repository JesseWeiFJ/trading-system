#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jtrader.datatype import *
from jtrader.core.common import logger, Registered
from jtrader.broker import BrokerInterface
from jtrader.trader.interface import TradingTemplate


class AlgorithmTemplate(TradingTemplate, Registered):

    def __init__(self, order: OrderData):
        super(AlgorithmTemplate, self).__init__()
        self._trading_mode = EnumTradingMode.AUTO
        self._target_order = order
        self._subject: BrokerInterface = BrokerInterface()
        self._sid = 0
        self._datetime = order.datetime
        logger.info('New algorithm is added for order %s', order)

    @property
    def target_order(self):
        return self._target_order

    @property
    def symbol(self):
        return self.target_order.symbol

    def get_price(self, price_level=0):
        return self.choose_price(self.target_order.symbol, self.target_order.direction, price_level)

    def _order_check(self, order: OrderData):
        result = super(AlgorithmTemplate, self)._order_check(order)
        if result:
            client_order_id = '-'.join((self.target_order.client_order_id, str(self._sid)))
            # client_order_id = order.client_order_id
            # order.parameter = {
            #     'sid': self._sid,
            #     'algorithm_id': self.target_order.client_order_id
            # }
            order.client_order_id = client_order_id
            self.target_order.order_id = client_order_id
            self.subscribe(EnumEventType.ORDER + client_order_id, self.on_order_status)
            self.subscribe(EnumEventType.TRADE + client_order_id, self.on_trade)
            self._sid += 1
        return result

    def on_order_status(self, order: OrderData):
        super(AlgorithmTemplate, self).on_order_status(order)
        if order.is_closed():
            self.unsubscribe(EnumEventType.ORDER + order.client_order_id, self.on_order_status)
            self.unsubscribe(EnumEventType.TRADE + order.client_order_id, self.on_trade)

    def on_trade(self, trade: TradeData):
        super(AlgorithmTemplate, self).on_trade(trade)
        logger.debug(f'{self} receive new execution volume {trade.volume}')
        trade_notional = trade.volume * trade.price
        self.target_order.executed_volume += trade.volume
        self.target_order.executed_notional += trade_notional

    @property
    def id_(self):
        return self._target_order.strategy_id

    def __repr__(self):
        return '{}({},{})'.format(
            self.__class__.__name__, self._target_order.symbol, self._target_order.client_order_id
        )

    def on_stop(self):
        super(AlgorithmTemplate, self).on_stop()
        self.cancel_all()
        order = self._target_order
        if not order.is_closed():
            order.status = EnumOrderStatus.CANCELLED
        self.broker.send(order)
        self.detach()
        self.set_mode(EnumTradingMode.OFF)

    def on_subscribe(self):
        order = self._target_order
        self.subscribe(EnumEventType.DEPTH + order.symbol, self.on_depth)
        self.subscribe(EnumEventType.BAR + order.symbol, self.on_bar)
        self.subscribe(EnumEventType.HEARTBEAT, self.on_heartbeat)


class AlgorithmFactory(object):
    def __new__(cls, target_order: OrderData) -> AlgorithmTemplate:
        algorithm_class = AlgorithmTemplate.subclass_dict[target_order.order_type]
        algorithm = algorithm_class(target_order)
        return algorithm
