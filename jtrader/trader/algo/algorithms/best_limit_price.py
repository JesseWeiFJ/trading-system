#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd
from jtrader.trader.algo.algorithm import AlgorithmTemplate
from jtrader.datatype import *
from jtrader.core.common.log import logger


class BestLimitPriceAlgorithm(AlgorithmTemplate):
    TAG = EnumOrderType.BLP

    def __init__(self, order: OrderData):
        super(BestLimitPriceAlgorithm, self).__init__(order)
        param_dict = order.parameter
        self.price_level = param_dict.get('price_level', 0)
        self.n_retry = param_dict.get('n_retry', 2)
        self.due_action = param_dict.get('due_action', EnumOrderStatus.CANCELLING)
        self._due_time = None
        self._is_due = False
        self._n_retried = 0
        self._client_order_id = ''

        self.duration = param_dict.get('duration', None)
        if self.duration is not None:
            self._due_time = pd.to_timedelta(self.duration, unit='s') + order.datetime

    def _on_due(self):
        if self.due_action == EnumOrderStatus.NEW:
            if self._client_order_id in self.working_order_dict:
                order = self.working_order_dict[self._client_order_id]
                self.cancel_order(self._client_order_id)
                self.price_level = -2
                self._resend_order()
        elif self.due_action == EnumOrderStatus.CANCELLING:
            self.on_stop()

    def on_heartbeat(self, heartbeat: HeartBeatData):
        super(BestLimitPriceAlgorithm, self).on_heartbeat(heartbeat)
        if self._due_time is not None:
            if heartbeat.datetime >= self._due_time:
                if self._is_due:
                    return
                self._is_due = True
                self._on_due()

    def _get_price(self):
        return self.get_price(self.price_level)

    def on_depth(self, depth: DepthData):
        super(BestLimitPriceAlgorithm, self).on_depth(depth)
        direction = self.target_order.direction
        if not self._client_order_id:
            volume = self.target_order.volume
            price = self._get_price()
            order = self.create_order(self.target_order.symbol, price, volume, direction, EnumOrderType.LIMIT)
            logger.debug(f'{self} send first order, return id {order.client_order_id}')
            self._client_order_id = order.client_order_id
        else:
            if self._client_order_id in self.working_order_dict and self._n_retried <= self.n_retry:
                working_order = self.working_order_dict[self._client_order_id]
                order_price = working_order.price
                best_price = self._get_price()
                if direction == EnumOrderDirection.BUY:
                    if order_price < best_price:
                        logger.debug(f'{self} got best buy price {best_price}, better than old price {order_price}')
                        self.cancel_order(self._client_order_id)
                        # self._client_order_id = ""
                        # this is a bug, if there is no client order id, then order would be resend repeatly
                else:
                    if order_price > best_price:
                        logger.debug(f'{self} got best sell price {best_price}, better than old price {order_price}')
                        self.cancel_order(self._client_order_id)
                        # self._client_order_id = ""

    def _resend_order(self):
        remain_volume = self.target_order.volume - self.target_order.executed_volume

        if not self.check_notional(self.symbol, remain_volume):
            self.on_stop()
            return

        if self._n_retried < self.n_retry:
            self._n_retried += 1
            logger.info(f'{self} retry No.{self._n_retried}')
            price = self._get_price()
            order = self.create_order(self.target_order.symbol, price, remain_volume,
                                      self.target_order.direction, EnumOrderType.LIMIT)
            self._client_order_id = order.client_order_id
        else:
            if self.due_action == EnumOrderStatus.CANCELLING:
                self.on_stop()
                return
            else:
                self.price_level = -2
                price = self._get_price()
                order = self.create_order(self.target_order.symbol, price, remain_volume,
                                          self.target_order.direction, EnumOrderType.LIMIT)
                self._client_order_id = order.client_order_id

    def on_order_status(self, order: OrderData):
        super(BestLimitPriceAlgorithm, self).on_order_status(order)
        status = order.status
        if order.is_closed():
            if (status == EnumOrderStatus.ERROR) or (status == EnumOrderStatus.CANCELLED):
                self._resend_order()
            else:
                self.target_order.status = status
                self.on_stop()
