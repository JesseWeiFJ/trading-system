#!/usr/bin/env python
# -*- coding: utf-8 -*-


from jtrader.core.common.log import logger
from jtrader.datatype import BarData
import copy
import pandas as pd


class VolumeBarGenerator(object):
    def __init__(self, symbol, volume, on_bar):
        self._symbol = symbol
        self._volume = volume
        self._volume_bar = None
        self._on_bar_func = on_bar

    def __repr__(self):
        return '%s(%s, %s)' % (
            self.__class__.__name__, self._symbol, self._volume
        )

    def update_bar(self, bar: BarData):
        if not self._volume_bar:
            self._volume_bar = copy.copy(bar)
            self._volume_bar.datetime.replace(second=0, microsecond=0)
            # self._volume_bar.frequency = ''
        else:
            self._volume_bar.close = bar.close
            self._volume_bar.high = max(self._volume_bar.high, bar.high)
            self._volume_bar.low = min(self._volume_bar.low, bar.low)
            self._volume_bar.volume += bar.volume

        if self._volume_bar.volume >= self._volume:
            self._on_bar_func(self._volume_bar)
            self._volume_bar = None
