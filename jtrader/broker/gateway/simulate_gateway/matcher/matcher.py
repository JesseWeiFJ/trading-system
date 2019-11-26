#!/usr/bin/env python
# -*- coding: utf-8 -*-
from jtrader.datatype import OrderData, TradeData, EnumEventType, DepthData, BarData
from jtrader.core.common import Registered, Subject
import typing


class Matcher(Registered):

    def __init__(self):
        super(Matcher, self).__init__()
        self.fee_rate = 0.0
        self.slippage = 0.0
        self.callback: typing.Callable = print

    def configure(self, matcher_config: dict):
        for key in matcher_config:
            if hasattr(self, key):
                setattr(self, key, matcher_config[key])
            # else:
            #     logger.info("%s has no %s attribute predefined", self, key)

    def match_order(self, order: OrderData):
        pass

    def on_depth(self, depth: DepthData):
        pass

    def on_bar(self, bar: BarData):
        pass
