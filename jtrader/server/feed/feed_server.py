#!/usr/bin/env python
# -*- coding: utf-8 -*-

from scikit_backtest.core import CubicDataArray
from jtrader.core.common import Singleton, Subject
from jtrader.datatype import *
from jtrader.server.feed.line import KLineManager

import typing


class FeedServer(object, metaclass=Singleton):

    def __init__(self, size=100):
        self._subject: Subject = None
        self._size = size
        self._kline_dict: typing.Dict[typing.Tuple[str, str], KLineManager] = {}

    def set_subject(self, subject):
        self._subject = subject
        self._subject.register(EnumEventType.BAR, self._on_bar)

    def get_kline(self, symbol, frequency):
        key = (symbol, frequency)
        if key not in self._kline_dict:
            kline = KLineManager(self._size)
            self._kline_dict[key] = kline
        return self._kline_dict[key]

    def _on_bar(self, bar: BarData):
        kline = self.get_kline(bar.symbol, bar.frequency)
        kline.on_bar(bar)

    def clear(self):
        self._kline_dict.clear()

    def get_cubic_data(self, symbol_list, frequency):
        kline_dict = {}
        latest_time = None

        for symbol in symbol_list:
            kline = self.get_kline(symbol, frequency)
            if not kline.inited:
                return
            kline_time = kline.time[-1]
            if latest_time is None:
                latest_time = kline_time
            elif latest_time != kline_time:
                return
            kline_dict[symbol] = kline

        df_dict = {k: v.to_df() for k, v in kline_dict.items()}
        return CubicDataArray.from_symbol_dict(df_dict)
