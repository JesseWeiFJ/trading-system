#!/usr/bin/env python
# -*- coding: utf-8 -*-
from abc import abstractmethod
import copy
from jtrader.core.common import Subject, Registered, Actor
from jtrader.core.common import logger
from jtrader.datatype import *
from jtrader.broker.oms import DataEngine
from jtrader.server import DatabaseServer


class BrokerInterface(Subject):

    def __repr__(self):
        return '%s()' % self.__class__.__name__

    def send_order(self, order: OrderData):
        pass
    
    def save_data(self, data: BaseData):
        pass

    def send(self, msg: BaseData):
        pass


class Broker(Registered, Actor, BrokerInterface):

    def __init__(self):
        super(Broker, self).__init__()
        self._event_process_map = {
            EnumEventType.DEPTH: self._process_depth_event,
            EnumEventType.BAR: self._process_bar_event,
            EnumEventType.TRADE: self._process_trade_event,
            EnumEventType.ORDER: self._process_order_event,
            EnumEventType.HEARTBEAT: self._process_heartbeat_event,
            EnumEventType.FUNDING: self._process_funding_event,
            EnumEventType.FUNDING_RATE: self._process_funding_rate_event,
        }
        self._data_engine = DataEngine()
        self._db_server: DatabaseServer = None

    def save_data(self, data):
        self._db_server.save(data)

    def set_db_server(self, db_server):
        self._db_server = db_server

    def handle_message(self, msg: BaseData):
        event_type = msg.EVENT_TYPE
        if event_type in self._event_process_map:
            process_func = self._event_process_map[event_type]
        else:
            process_func = self._process_general_event
        try:
            process_func(msg)
        except Exception as e:
            logger.exception(e)
            logger.info(f'Error occurred when handling {msg}')
            raise e

    def send_order(self, order: OrderData):
        logger.debug(f'{self} plan to send {order.pretty_string()}')
        self._send_order_impl(copy.copy(order))

    @abstractmethod
    def _send_order_impl(self, order: OrderData):
        pass

    def query_balance(self, exchange=None, currency=None):
        pass

    def query_bar(self, exchange=None, count=100):
        pass

    def query_data(self, name, query=None, columns=None):
        return self._data_engine.query_data(name, query, columns)

    def configure(self, broker_config: dict):
        pass

    # -------------------- process event --------------------------
    def _process_general_event(self, event: BaseData):
        self.notify(event.EVENT_TYPE, event)

    def _process_bar_event(self, bar: BarData):
        self._data_engine.on_bar(bar)

        symbol = bar.symbol
        self.notify(bar.EVENT_TYPE, bar)
        self.notify(bar.EVENT_TYPE + symbol, bar)

    def _process_depth_event(self, depth: DepthData):
        self._data_engine.on_depth(depth)
        symbol = depth.symbol
        self.notify(depth.EVENT_TYPE, depth)
        self.notify(depth.EVENT_TYPE + symbol, depth)

    def _process_order_event(self, order: OrderData):
        self._data_engine.on_order_status(order)
        self.save_data(order)
        self.notify(order.EVENT_TYPE, order)
        self.notify(order.EVENT_TYPE + order.strategy_id, order)  # for strategy
        self.notify(order.EVENT_TYPE + order.client_order_id, order)  # for algorithm

    def _process_trade_event(self, trade: TradeData):
        if self._data_engine.on_trade(trade):
            self.save_data(trade)
            self.notify(trade.EVENT_TYPE, trade)
            self.notify(trade.EVENT_TYPE + trade.strategy_id, trade)  # for strategy
            self.notify(trade.EVENT_TYPE + trade.client_order_id, trade)  # for algorithm

    def _process_funding_event(self, funding: FundingData):
        self._data_engine.on_funding(funding)
        self.notify(funding.EVENT_TYPE, funding)
        self.notify(funding.EVENT_TYPE + funding.strategy_id, funding)

    def _process_heartbeat_event(self, heartbeat: HeartBeatData):
        self.notify(heartbeat.EVENT_TYPE, heartbeat)
        if heartbeat.frequency != '1s':
            self.notify(heartbeat.EVENT_TYPE + heartbeat.frequency, heartbeat)

    def _process_funding_rate_event(self, funding_rate: FundingRateData):
        self.notify(funding_rate.EVENT_TYPE, funding_rate)
        self.notify(funding_rate.EVENT_TYPE + funding_rate.symbol, funding_rate)
