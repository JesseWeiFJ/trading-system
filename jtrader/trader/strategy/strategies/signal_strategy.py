#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scikit_backtest.features.signal import TradingSignal
from scikit_backtest.position import LongShortSignalPositioner
from jtrader.trader.strategy.strategy import StrategyTemplate
from jtrader.server.feed import FeedServer
from jtrader.datatype import *
import pandas as pd


class SignalStrategy(StrategyTemplate):
    def __init__(self, signal: TradingSignal, frequency='1h', shortable=True):
        super(SignalStrategy, self).__init__()
        self.signal = signal
        self.frequency = frequency
        self.shortable = shortable
        self._symbol = ''

    def on_init(self):
        super(SignalStrategy, self).on_init()
        if len(self.universe) != 1:
            raise TypeError('Universe should be of length 1, got {:d} instead'.format(len(self.universe)))
        self._symbol = self.universe[0]

    @property
    def cash(self):
        return self.portfolio.get_cash_value()

    @property
    def asset(self):
        return self.portfolio.available_base_amount(self._symbol)

    def _buy(self):
        direction = EnumOrderDirection.BUY
        price = self.choose_price(self._symbol, direction)
        volume = self.cash / price
        if self.check_notional(self._symbol, volume):
            self.create_order(self._symbol, price, volume, direction, EnumOrderType.BLP)

    def _sell(self):
        direction = EnumOrderDirection.SELL
        price = self.choose_price(self._symbol, direction)
        volume = self.asset
        if self.check_notional(self._symbol, volume):
            self.create_order(self._symbol, price, volume, direction, EnumOrderType.BLP)

    def on_bar(self, bar):
        super(SignalStrategy, self).on_bar(bar)
        if bar.frequency == self.frequency and bar.symbol == self._symbol:
            kline = FeedServer().get_kline(self._symbol, self.frequency)
            if not kline.inited:
                return

            self.cancel_all()
            bar_df = kline.to_df()
            # pred = self.signal.predict(bar_df)[-1]
            result = self.signal.predict(bar_df)
            pred = LongShortSignalPositioner(self.shortable).transform(result)[-1]

            # up cross
            if pred == 1:
                self._buy()
            # down cross
            elif pred == -1:
                self._sell()

    def get_market_signal(self):
        status = super(SignalStrategy, self).get_market_signal()
        df = FeedServer().get_kline(self._symbol, self.frequency).to_df()
        signal = self.signal.predict(df)
        signal_statement = 'Last 5 signals:\n{}'.format(signal.tail(5).to_string())
        status = '\n'.join([status, signal_statement])
        return status


class SwapSignalStrategy(SignalStrategy):

    def _buy(self):
        direction = EnumOrderDirection.BUY
        price = self.choose_price(self._symbol, direction, 1)
        volume = self.cash
        if self.cash >= 0 and self.check_notional(self._symbol, volume):
            self.create_order(self._symbol, price, volume, direction, EnumOrderType.LIMIT)

    def _sell(self):
        direction = EnumOrderDirection.SELL
        price = self.choose_price(self._symbol, direction, 1)
        asset = self.portfolio[self._symbol].amount
        target = - (asset + self.cash)
        volume = - (target - asset)
        if self.asset >= 0 and self.check_notional(self._symbol, volume):
            self.create_order(self._symbol, price, volume, direction, EnumOrderType.LIMIT)
