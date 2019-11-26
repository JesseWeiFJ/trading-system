#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jtrader.broker.gateway import Gateway
from jtrader.broker.gateway.simulate_gateway.matcher import Matcher, MatcherFactory

from jtrader.datatype import *


class SimulateGateway(Gateway):
    TAG = ExchangeAbbr.SIMULATE

    def __init__(self):
        super(SimulateGateway, self).__init__()
        self._matcher: Matcher = None

        self.fee_rate = 0.0
        self.slippage = 0.0

    def configure(self, gateway_config: dict = None):
        matcher_config = gateway_config['matcher']
        matcher_type = matcher_config['matcher_type']
        self._matcher = MatcherFactory(matcher_type)
        self._matcher.configure(matcher_config)
        self._matcher.callback = self.callback

    def set_callback(self, callback):
        super(SimulateGateway, self).set_callback(callback)
        if self._matcher is not None:
            self._matcher.callback = self.callback

    def query_bar(self, *args, **kwargs):
        return []

    def send_order(self, order: OrderData):
        self._matcher.match_order(order)

    def on_depth(self, depth: DepthData):
        self._matcher.on_depth(depth)

    def on_bar(self, bar: BarData):
        self._matcher.on_bar(bar)
