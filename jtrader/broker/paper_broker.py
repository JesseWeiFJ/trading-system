#!/usr/bin/env python
# -*- coding: utf-8 -*-
from jtrader.datatype import *
from jtrader.broker.real_broker import RealBroker
from jtrader.broker.gateway.simulate_gateway import SimulateGateway


class PaperBroker(RealBroker):
    TAG = 'paper'

    def __init__(self):
        super(PaperBroker, self).__init__()
        self._bt_gateway: SimulateGateway = None

    def configure(self, broker_config: dict):
        super(PaperBroker, self).configure(broker_config)
        self._bt_gateway: SimulateGateway = self._gateway_dict[ExchangeAbbr.SIMULATE]

        self.register(EnumEventType.BAR, self._bt_gateway.on_bar)
        self.register(EnumEventType.DEPTH, self._bt_gateway.on_depth)

    def _send_order_impl(self, order: OrderData):
        self._bt_gateway.send_order(order)
