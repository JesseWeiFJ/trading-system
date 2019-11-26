#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import defaultdict
from jtrader.trader.strategy.risk import RiskControl
from jtrader.core.common.log import logger
from jtrader.datatype import EnumTradingMode
from jtrader.trader.strategy.strategy import StrategyTemplate


class MaxDrawdownControl(RiskControl):
    TAG = 'max_drawdown'

    def __init__(self, stop_loss=0.10):
        super(MaxDrawdownControl, self).__init__()
        self.stop_loss = stop_loss
        self._max_pnl_dict = defaultdict(float)

    def check_risk(self, strategy: StrategyTemplate):
        strategy.update_portfolio()
        pnl = strategy.portfolio.pnl

        present_pnl = pnl.total_pnl
        max_pnl = self._max_pnl_dict[strategy.id_]
        if present_pnl > max_pnl:
            self._max_pnl_dict[strategy.id_] = present_pnl

        if pnl.asset_value:
            pnl_ratio = (present_pnl - max_pnl) / pnl.asset_value
            if pnl_ratio < -abs(self.stop_loss):
                logger.warning(f'{self} triggered with pnl rate {pnl_ratio}\n{pnl.pretty_string()}')
                strategy.close_all()
                strategy.set_mode(EnumTradingMode.OFF)
