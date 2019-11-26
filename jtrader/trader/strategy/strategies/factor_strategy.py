#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd
from scikit_backtest.features.factor import AlphaFactor

from jtrader.trader.strategy import StrategyTemplate
from jtrader.server import FeedServer
from jtrader.core.common import logger
from jtrader.datatype import *


class FactorStrategy(StrategyTemplate):
    def __init__(
            self, factor, frequency='1h', top_count=2, price_level=0
    ):
        super(FactorStrategy, self).__init__()
        self.factor: AlphaFactor = factor
        self.frequency = frequency
        self.top_count = top_count
        self.price_level = price_level

        self._to_hold = []
        self._factor_series = pd.Series()

    def on_bar(self, bar):
        super(FactorStrategy, self).on_bar(bar)
        if (bar.symbol in self.universe) and (bar.frequency == self.frequency):
            cubic_data = self._get_cubic_data()
            if cubic_data:
                self._trade_by_cubic_data(cubic_data)

    def get_cross_symbol(self, symbol):
        return symbol

    def _get_cross_symbol_list(self, symbol_list):
        cross_symbol_list = []
        for symbol in symbol_list:
            cross_symbol = self.get_cross_symbol(symbol)
            cross_symbol_list.append(cross_symbol)
        return cross_symbol_list

    def _get_cubic_data(self):
        return FeedServer().get_cubic_data(self.universe, self.frequency)

    def _trade_by_cubic_data(self, cubic_data):
        self.cancel_all()

        factor_df = self.factor.predict(cubic_data)
        factor_series = factor_df.iloc[-1].sort_values().dropna()

        to_buy_list = list(factor_series.iloc[-self.top_count:].index)
        self._to_hold = to_buy_list
        self._factor_series = factor_series

        if self.trading_mode < EnumTradingMode.AUTO:
            logger.info('{} not in auto trading mode: {}'.format(self, self.trading_mode.name))
            return

        to_buy_set = set(self._get_cross_symbol_list(to_buy_list))
        logger.info('{} plan to hold {}'.format(self, to_buy_set))

        available_cash = self.portfolio.get_cash_value()
        for position in self.portfolio:
            direction = EnumOrderDirection.SELL
            symbol = position.symbol
            # volume = self.portfolio[symbol].amount
            volume = self.portfolio.available_base_amount(symbol)
            if volume > 0 and self.check_notional(symbol, volume):
                if symbol in to_buy_set:
                    to_buy_set.remove(symbol)
                else:
                    available_cash += position.asset_value
                    self._trade(symbol, direction, volume)

        # cash will be get after seconds in real time trading
        if len(to_buy_set):
            value = available_cash / len(to_buy_set)
            direction = EnumOrderDirection.BUY
            for symbol in to_buy_set:
                price = self.choose_price(symbol, direction, self.price_level)
                volume = value / price
                if volume > 0 and self.check_notional(symbol, volume):
                    self._trade(symbol, direction, volume)

    def _trade(self, symbol, direction, volume):
        price = self.choose_price(symbol, direction, 0)
        tick = ContractData.get_contract(symbol).tick_size
        n_retry = 2
        if direction == EnumOrderDirection.BUY:
            # requirement = {
            #     'price_level': self.price_level,
            #     'n_retry': n_retry,
            #     'duration': TIME_INTERVAL_MAP[self.frequency].total_seconds() * 0.5,
            #     'due_action': EnumOrderStatus.CANCELLING,
            # }
            price += tick
            self.create_order(
                symbol,
                price,
                volume,
                direction,
                EnumOrderType.LIMIT,
                # EnumOrderType.BLP,
                # requirement=requirement,
            )

        else:
            # requirement = {
            #     'price_level': self.price_level,
            #     'n_retry': n_retry,
            #     'duration': TIME_INTERVAL_MAP[self.frequency].total_seconds() * 0.5,
            #     'due_action': EnumOrderStatus.NEW,
            # }
            price -= tick * 2
            self.create_order(
                symbol,
                price,
                volume,
                direction,
                EnumOrderType.LIMIT,
                # EnumOrderType.BLP,
                # requirement=requirement,
            )

    def get_market_signal(self):
        cubic_data = self._get_cubic_data()
        if cubic_data:
            latest_time = cubic_data.datetime[-1]
            bar_df = cubic_data.select_datetime(latest_time)
            bar_df['factor'] = self._factor_series
            bar_str = bar_df.to_string()
            time_str = 'Period: ' + str(latest_time)
            to_buy_str = 'Holding: ' + str(self._to_hold)
            market_str = '\n'.join([bar_str, time_str, to_buy_str])
            return market_str
        return 'Holding: ' + str(self._to_hold)
