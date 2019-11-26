#!/usr/bin/env python
# -*- coding: utf-8 -*-
from jtrader.core.common import logger
from jtrader.datatype import *
from jtrader.broker.gateway import Gateway, GatewayFactory
from jtrader.broker.broker import Broker
from jtrader.core.tools.scheduler.timer import Timer

from concurrent.futures import ThreadPoolExecutor
import typing


class RealBroker(Broker):

    TAG = 'real'

    def __init__(self):
        super(RealBroker, self).__init__()
        self._gateway_dict: typing.Dict[str, Gateway] = {}
        self._executor = ThreadPoolExecutor(10)
        self._timer = Timer()
        self._timer.register(EnumEventType.HEARTBEAT, self.send)

    def _process_order_request(self, order: OrderData):
        exchange = order.contract.exchange
        if exchange in self._gateway_dict:
            gateway = self._gateway_dict[exchange]
            logger.debug('%s send %s', gateway, order)
            gateway.send_order(order)
        else:
            logger.info("No such %s gateway exist", exchange)

    def _send_order_impl(self, order: OrderData):
        self._executor.submit(self._process_order_request, order)

    def query_balance(self, exchange=None, currency=None):
        return self._gateway_dict[exchange].query_balance(currency)

    def query_bar(self, exchange=None, count=100):
        return self._gateway_dict[exchange].query_bar(count)

    def configure(self, broker_config: dict):
        super(RealBroker, self).configure(broker_config)
        for gateway_name, gateway_config in broker_config['gateway'].items():
            gateway = GatewayFactory(gateway_name)
            gateway.set_callback(self.send)
            gateway.configure(gateway_config)
            self._gateway_dict[gateway_name] = gateway
            logger.info('%s configuration finished', gateway)

    def start(self):
        super(RealBroker, self).start()
        self._executor = ThreadPoolExecutor(10)
        for _, gateway in self._gateway_dict.items():
            gateway.start()
        self._timer.start()

    def stop(self):
        super(RealBroker, self).stop()
        for _, gateway in self._gateway_dict.items():
            gateway.stop()
        self._executor.shutdown()
        self._timer.stop()
