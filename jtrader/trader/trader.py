#!/usr/bin/env python
# -*- coding: utf-8 -*-
import typing

from jtrader.datatype import *
from jtrader.core.common import logger

from jtrader.broker import Broker
from jtrader.trader.strategy import StrategyTemplate, StrategyConfigInfo, StrategyFactory
from jtrader.trader.algo import AlgorithmEngine


class Trader(object):
    def __init__(self):
        super(Trader, self).__init__()
        self._broker: Broker = None
        self._strategy_dict: typing.Dict[str, StrategyTemplate] = {}
        self._algorithm_engine = AlgorithmEngine()

    def _persist_portfolio(self, heartbeat: HeartBeatData):
        for id_, strategy in self.strategy_dict.items():
            strategy.update_portfolio()
            pnl = strategy.portfolio.pnl
            pnl.datetime = heartbeat.datetime
            self._broker.save_data(pnl)
            for position in strategy.portfolio:
                self._broker.save_data(position)
            for balance in strategy.portfolio._balance_dict.values():
                self._broker.save_data(balance)

    def configure(self, trader_config: dict):
        for strategy_config in trader_config['strategy']:
            strategy = self.create_strategy(strategy_config)
            self.add_strategy(strategy)

    def set_broker(self, broker: Broker):
        self._broker = broker
        self._broker.register(EnumEventType.HEARTBEAT + '30m', self._persist_portfolio)

        self._algorithm_engine.set_broker(broker)

    def send_order(self, order: OrderData):
        self._algorithm_engine.send_order(order)

    @property
    def strategy_dict(self):
        return self._strategy_dict

    def add_strategy(self, strategy: StrategyTemplate):
        id_ = strategy.id_
        if id_ not in self._strategy_dict:
            self._strategy_dict[id_] = strategy
            strategy.attach_with(self._broker)
            strategy.algorithm_engine = self._algorithm_engine
            logger.info('%s was added to %s', strategy, self)
        else:
            logger.info('%s already exists in %s', strategy, self)

    def remove_strategy(self, id_: str):
        if id_ in self._strategy_dict:
            strategy = self._strategy_dict[id_]
            strategy.detach()
            del self._strategy_dict[id_]
            logger.info('%s was removed from %s', strategy, self)

    def modify_strategy(self, strategy_config: dict):
        strategy_info = StrategyConfigInfo.from_dict(strategy_config)
        strategy_id = strategy_info.strategy_id
        if strategy_id in self.strategy_dict:
            strategy = self.strategy_dict[strategy_id]
            strategy.configure(strategy_info)
        else:
            logger.info('There is no such strategy exist with id %s', strategy_id)

    @classmethod
    def create_strategy(cls, strategy_config: dict):
        strategy_info = StrategyConfigInfo.from_dict(strategy_config)
        strategy = StrategyFactory(strategy_info.strategy_type)
        strategy.configure(strategy_info)
        return strategy
    
    def query_algorithms(self):
        return self._algorithm_engine.get_running_status()

