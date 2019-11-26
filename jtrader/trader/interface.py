#!/usr/bin/env python
# -*- coding: utf-8 -*-
from jtrader.datatype import *
from jtrader.core.common import Subscriber, logger
from jtrader.broker import BrokerInterface
import typing
import copy
import datetime


class TradingTemplate(Subscriber):

    @property
    def datetime(self):
        return self._datetime

    @property
    def trading_mode(self):
        return self._trading_mode

    @property
    def working_order_dict(self):
        return self._working_order_dict

    @property
    def id_(self):
        return ''

    @property
    def broker(self):
        return self._subject

    @property
    def depth_dict(self):
        return self._depth_dict

    @property
    def bar_dict(self):
        return self._bar_dict

    def __init__(self):
        super(TradingTemplate, self).__init__()
        self._subject = BrokerInterface()
        self._datetime = datetime.datetime.utcnow()
        self._working_order_dict: typing.Dict[str, OrderData] = {}
        self._trading_mode = EnumTradingMode.OFF

        self._depth_dict: typing.Dict[str, DepthData] = {}
        self._bar_dict: typing.Dict[str, BarData] = {}

    def set_mode(self, mode):
        if isinstance(mode, EnumTradingMode):
            logger.info('%s mode changed: %s --> %s', self, self._trading_mode, mode)
            self._trading_mode = mode

    def on_init(self):
        pass

    def on_stop(self):
        pass

    def on_bar(self, bar: BarData):
        self._bar_dict[bar.symbol] = bar

    def on_depth(self, depth: DepthData):
        self._depth_dict[depth.symbol] = depth

    def on_order_status(self, order: OrderData):
        client_order_id = order.client_order_id
        status = order.status
        if client_order_id in self._working_order_dict:
            self._working_order_dict[client_order_id].on_order(order)
            if order.is_closed():
                del self._working_order_dict[client_order_id]
            elif status == EnumOrderStatus.CANCEL_ERROR:
                order.status = EnumOrderStatus.PENDING
        else:
            if not order.is_closed():
                self._working_order_dict[client_order_id] = copy.copy(order)

    def on_trade(self, trade: TradeData):
        pass

    def on_funding(self, funding: FundingData):
        pass

    def on_heartbeat(self, heartbeat: HeartBeatData):
        self._datetime = heartbeat.datetime

    def choose_price(self, symbol: str, direction: EnumOrderDirection, price_level: int = 0):
        if price_level < 0:
            direction = - direction
            price_level = - price_level - 1
        if symbol in self._depth_dict:
            depth = self._depth_dict[symbol]
            if direction == EnumOrderDirection.BUY:
                price = depth.bid_prices[price_level]
            else:
                price = depth.ask_prices[price_level]
            return price
        elif symbol in self._bar_dict:
            price = self._bar_dict[symbol].close
            return price
        return 0.0

    def create_order(self, symbol, price, volume, direction, order_type, requirement: dict = None):
        order = self._create_order_impl(symbol, price, volume, direction, order_type, requirement)
        result = self._order_check(order)
        if result:
            self.working_order_dict[order.client_order_id] = order
            self.broker.send_order(order)
        else:
            order.status = EnumOrderStatus.REJECTED
        return order

    def cancel_all(self):
        id_list = tuple(self.working_order_dict.keys())
        for client_order_id in id_list:
            self.cancel_order(client_order_id)

    def cancel_order(self, client_order_id):
        if not self._trading_mode:
            logger.info('Cancel request not send, Reason: %s is in trading state %s', self, self._trading_mode)
            return

        if client_order_id not in self._working_order_dict:
            logger.debug('Cancel request not send, Reason: order %s is not in working order list',
                         client_order_id)
            return

        working_order = self._working_order_dict[client_order_id]

        if working_order.is_closed():
            logger.info('Cancel request not send, Reason: order %s is already finished with status %s',
                        working_order.client_order_id, working_order.status)
            return

        if working_order.status == EnumOrderStatus.CANCELLING:
            logger.debug('Cancel request not send, Reason: order %s has been sent before', client_order_id)
            return

        if not working_order.order_id:
            logger.info('Cancel request not send, Reason: order %s is not alive in exchange yet (no order id)',
                        client_order_id)
            return

        cancel_req = copy.copy(working_order)
        cancel_req.status = EnumOrderStatus.CANCELLING
        logger.debug('%s cancel order with client order id %s', self, client_order_id)
        self.broker.send_order(cancel_req)

    def order(self, symbol, volume, price_level=-2):
        if volume > 0:
            direction = EnumOrderDirection.BUY
        else:
            direction = EnumOrderDirection.SELL
        price = self.choose_price(symbol, direction, price_level)
        return self.create_order(symbol, price, abs(volume), direction, EnumOrderType.LIMIT)

    def _order_check(self, order: OrderData):
        if self._trading_mode <= EnumTradingMode.OFF:
            logger.info('Request not send: %s is in trading state %s', self, self._trading_mode)
            return False
        return order.contract_check()

    def check_notional(self, symbol, volume):
        price = self.choose_price(symbol, EnumOrderDirection.BUY, 0)
        order = self._create_order_impl(symbol, price, volume)
        return order.contract_check()

    def _create_order_impl(self, symbol, price, volume,
                           direction=EnumOrderDirection.BUY,
                           order_type=EnumOrderType.LIMIT,
                           requirement: dict = None):
        order = OrderData()
        order.symbol = symbol
        order.price = price
        order.volume = volume
        order.status = EnumOrderStatus.NEW
        order.direction = direction
        order.order_type = order_type
        order.strategy_id = self.id_
        order.datetime = self.datetime
        if requirement is not None:
            order.parameter = requirement
        return order
