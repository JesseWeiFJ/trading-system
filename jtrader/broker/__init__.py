#!/usr/bin/env python
# -*- coding: utf-8 -*-


from .bt_broker import BackTestBroker
from .paper_broker import PaperBroker
from .real_broker import RealBroker
from .broker import Broker, BrokerInterface


class BrokerFactory(object):
    def __new__(cls, name, broker_config=None) -> Broker:
        _instance: Broker = Broker.factory_create(name)
        if broker_config:
            _instance.configure(broker_config)
        return _instance
