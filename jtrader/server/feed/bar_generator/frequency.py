#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jtrader.core.common.log import logger
from jtrader.datatype import BarData
import copy
import pandas as pd


class FrequencyBarGenerator(object):
    def __init__(self, symbol, freq, on_bar):
        self._symbol = symbol
        self._freq = freq
        self._on_bar_func = on_bar
        self._n_min = int(pd.to_timedelta(freq).total_seconds() / 60)
        self._n_min_bar = None

    def __repr__(self):
        return '%s(%s, %s)' % (
            self.__class__.__name__, self._symbol, self._freq
        )

    def update_bar(self, bar: BarData):
        logger.debug('%s get bar %s', self, bar)
        if not self._n_min_bar:
            self._n_min_bar = copy.copy(bar)
            self._n_min_bar.datetime.replace(second=0, microsecond=0)
            self._n_min_bar.freq = self._freq
        else:
            self._n_min_bar.close = bar.close
            self._n_min_bar.high = max(self._n_min_bar.high, bar.high)
            self._n_min_bar.low = min(self._n_min_bar.low, bar.low)
            self._n_min_bar.volume += bar.volume

        if not (bar.datetime.minute + 1) % self._n_min:
            self._on_bar_func(self._n_min_bar)
            self._n_min_bar = None
