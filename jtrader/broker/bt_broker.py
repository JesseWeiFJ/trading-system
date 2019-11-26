#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime

from jtrader.datatype import *
from jtrader.broker.broker import Broker
from jtrader.broker.gateway.simulate_gateway import SimulateGateway


class BackTestBroker(Broker):
    TAG = 'bt'

    def __init__(self):
        super(BackTestBroker, self).__init__()
        self._gateway: SimulateGateway = None
        self._event_list = []

    def save_data(self, data):
        pass

    def send(self, msg):
        self.handle_message(msg)

    def configure(self, broker_config: dict):
        super(BackTestBroker, self).configure(broker_config)
        gateway_config = broker_config['gateway'][SimulateGateway.TAG]
        gateway = SimulateGateway()
        gateway.configure(gateway_config)
        gateway.set_callback(self.send)

        self.register(EnumEventType.BAR, gateway.on_bar)
        self.register(EnumEventType.DEPTH, gateway.on_depth)

        self._gateway = gateway
        self._event_list = broker_config['event_list']

    def _send_order_impl(self, order: OrderData):
        self._gateway.send_order(order)

    def start(self):
        dt = datetime.datetime(1970, 1, 1)
        frequency = '1m'
        for event in self._event_list:
            if event.EVENT_TYPE == EnumEventType.BAR:
                event_dt = event.settle_time()
                frequency = event.frequency
            else:
                event_dt = event.datetime

            if event_dt > dt:
                heartbeat = HeartBeatData(datetime=dt)
                heartbeat.frequency = frequency
                self.handle_message(heartbeat)

                dt = event_dt
                heartbeat = HeartBeatData(datetime=dt)
                heartbeat.frequency = frequency
                self.handle_message(heartbeat)

                if frequency != '1m':
                    heartbeat = heartbeat.copy()
                    heartbeat.frequency = '1m'
                    self.handle_message(heartbeat)
            self.handle_message(event)

    def stop(self):
        pass
