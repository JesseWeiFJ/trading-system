#!/usr/bin/env python
# -*- coding: utf-8 -*-
import typing
from jtrader.datatype import *
from jtrader.trader.algo.algorithm import AlgorithmFactory, AlgorithmTemplate
from jtrader.broker import BrokerInterface


class AlgorithmEngine(BrokerInterface):

    def __init__(self):
        super(AlgorithmEngine, self).__init__()
        self._broker: BrokerInterface = None
        self._algorithm_dict: typing.Dict[str, AlgorithmTemplate] = {}

    def send_order(self, order: OrderData):
        if order.order_type in ORIGIN_ORDER_TYPES:
            return self._broker.send_order(order)

        cli_id = order.client_order_id

        if order.status == EnumOrderStatus.NEW:
            algorithm = AlgorithmFactory(order)
            algorithm.attach_with(self._broker)
            self._algorithm_dict[cli_id] = algorithm
        else:
            if cli_id in self._algorithm_dict:
                algorithm = self._algorithm_dict[cli_id]
                algorithm.on_stop()
                self._algorithm_dict.pop(cli_id)

    def set_broker(self, broker: BrokerInterface):
        self._broker = broker
        self._broker.register(EnumEventType.ORDER, self._on_order_status)

    def _on_order_status(self, order: OrderData):
        cli_id = order.client_order_id
        if cli_id in self._algorithm_dict:
            if order.is_closed():
                self._algorithm_dict.pop(cli_id)

    def get_running_status(self):
        string_list = []
        template = "%s\n" \
                   "execution:\n%s"
        for algorithm_id, algorithm in self._algorithm_dict.items():
            string_list.append(
                template % (algorithm, algorithm.target_order.pretty_string())
            )
        return '\n'.join(string_list)
