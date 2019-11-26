#!/usr/bin/env python
# -*- coding: utf-8 -*-
import typing

from jtrader.datatype import *
from jtrader.core.common.log import logger
from jtrader.core.common.template import Subscriber
from jtrader.datatype.portfolio import Portfolio


class DataEngine(object):

    def __repr__(self):
        return '%s()' % self.__class__.__name__

    def __init__(self):
        super(DataEngine, self).__init__()
        self._portfolio = Portfolio('OMS')
        self._bar_dict: typing.Dict[str, BarData] = {}
        self._depth_dict: typing.Dict[str, DepthData] = {}
        self._order_dict: typing.Dict[str, OrderData] = {}
        self._trade_dict: typing.Dict[typing.Tuple, TradeData] = {}
        self._funding_dict: typing.Dict[str, FundingData] = {}

    def update_portfolio(self, symbol=None):
        if symbol is not None:
            if symbol in self._bar_dict:
                self._portfolio.on_bar(self._bar_dict[symbol])
            if symbol in self._depth_dict:
                self._portfolio.on_depth(self._depth_dict[symbol])
            return
        for symbol, bar in self._bar_dict.items():
            self._portfolio.on_bar(bar)
        for symbol, depth in self._depth_dict.items():
            self._portfolio.on_depth(depth)

    def on_depth(self, depth: DepthData):
        self._depth_dict[depth.symbol] = depth

    def on_bar(self, bar: BarData):
        self._bar_dict[bar.symbol] = bar

    def on_funding(self, funding: FundingData):
        if funding.funding_id not in self._funding_dict:
            self._funding_dict[funding.funding_id] = funding
            self._portfolio.on_funding(funding)
            logger.info("%s receive %s", self, funding.pretty_string())

    def on_order_status(self, order: OrderData):
        client_order_id = order.client_order_id
        # the order should be sent by OMS before
        if client_order_id in self._order_dict:
            local_order = self._order_dict[client_order_id]

            # order was in active mode
            if not local_order.is_closed():
                self._order_dict[client_order_id].on_order(order)
                self._portfolio.on_order_status(order)

            # order was already closed before
            else:
                order = local_order
        else:
            self._order_dict[order.client_order_id] = order

        logger.info("%s receive %s", self, order.pretty_string())
        return

    def on_trade(self, trade: TradeData):
        key = (trade.client_order_id, trade.trade_id)
        if key in self._trade_dict:
            return False
        else:
            self._trade_dict[key] = trade
            self._portfolio.on_trade(trade)
            logger.info("%s receive %s", self, trade.pretty_string())
            return True

    def query_data(self, name, condition: str = None, columns=None):
        if name == 'portfolio':
            self.update_portfolio()
            data_list = list(self._portfolio)
        elif name == 'bar':
            data_list = self._bar_dict.values()
        elif name == 'depth':
            data_list = self._depth_dict.values()
        elif name == 'order':
            data_list = self._order_dict.values()
        elif name == 'trade':
            data_list = self._trade_dict.values()
        elif name == 'funding':
            data_list = self._funding_dict.values()
        else:
            raise ValueError('No %s data in %s' % (name, self))

        data_df = BaseData.to_df(data_list)
        if condition:
            if condition.startswith('+'):
                data_df = data_df.head(int(condition[1:]))
            elif condition.startswith('-'):
                data_df = data_df.tail(int(condition[1:]))
            else:
                data_df = data_df.query(condition)
        if columns:
            data_df = data_df[columns]
        return data_df
