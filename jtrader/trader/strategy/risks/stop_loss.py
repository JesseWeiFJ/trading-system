#!/usr/bin/env python
# -*- coding: utf-8 -*-
from jtrader.trader.strategy.risk import RiskControl
from jtrader.core.common.log import logger
from jtrader.datatype.markets import ContractData
from jtrader.trader.strategy.strategy import StrategyTemplate


class StopLossControl(RiskControl):

    TAG = 'stop_loss'

    def __init__(self, stop_loss=0.02):
        super(StopLossControl, self).__init__()
        self.stop_loss = stop_loss

    def check_risk(self, strategy: StrategyTemplate):
        strategy.update_portfolio()
        for position in strategy.portfolio:
            symbol = position.symbol
            pnl_ratio = position.unrealized_pnl_rate()
            contract = ContractData.get_contract(symbol)
            if (abs(position.amount) > contract.min_quantity) and (pnl_ratio < -abs(self.stop_loss)):
                logger.info(f'Stop loss triggered by {self} with pnl rate {pnl_ratio}\n{position.pretty_string()}')
                strategy.close_position(position.symbol)
