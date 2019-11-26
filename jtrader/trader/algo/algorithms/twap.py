#!/usr/bin/env python
# -*- coding: utf-8 -*-
from jtrader.trader.algo.algorithm import AlgorithmTemplate
from jtrader.datatype import *
import pandas as pd
import datetime


class TWAPAlgorithm(AlgorithmTemplate):
    TAG = EnumOrderType.TWAP

    def __init__(self, order: OrderData):
        super(TWAPAlgorithm, self).__init__(order)
        param_dict = order.parameter
        self.execute_interval = pd.to_timedelta(param_dict['execute_interval'])
        self.execute_times = param_dict['execute_times']
        self._last_execute_time = datetime.datetime.fromtimestamp(0)
        self._part_volume = self.target_order.volume / self.execute_times
        self._executed_times = 0

    def _execute_part_order(self):
        target_order = self.target_order
        self.create_order(target_order.symbol, 0, self._part_volume,
                          target_order.direction, EnumOrderType.MARKET)

    def on_heartbeat(self, heartbeat: HeartBeatData):
        super(TWAPAlgorithm, self).on_heartbeat(heartbeat)
        if self.datetime - self._last_execute_time > self.execute_interval:
            if self._executed_times < self.execute_times:
                self._executed_times += 1
                self._last_execute_time = self.datetime
                self._execute_part_order()

    def on_order_status(self, order: OrderData):
        super(TWAPAlgorithm, self).on_order_status(order)
        if order.is_closed():
            if self._executed_times >= self.execute_times:
                self.target_order.status = order.status
                self.on_stop()
