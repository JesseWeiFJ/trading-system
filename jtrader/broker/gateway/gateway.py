#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jtrader.datatype import *
import typing
from jtrader.core.common.template import Registered


class Gateway(Registered):

    def __init__(self):
        self.callback: typing.Callable[[BaseData], None] = print

    def set_callback(self, callback):
        self.callback = callback

    def configure(self, gateway_config: dict = None):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def subscribe(self, symbol, frequency='1m'):
        pass

    # ---------------- request ----------------
    def query_balance(self, currency=None):
        pass

    def query_bar(self, symbol, frequency='1m', count=100):
        pass

    def send_order(self, order: OrderData):
        pass


class GatewayFactory(object):
    def __new__(cls, name) -> Gateway:
        _instance = Gateway.factory_create(name)
        return _instance
