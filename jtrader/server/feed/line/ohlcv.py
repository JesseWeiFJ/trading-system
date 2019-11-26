# encoding: UTF-8

from jtrader.datatype import BarData
import numpy as np
import pandas as pd
from collections import deque

try:
    import talib
except ImportError:
    pass


class KLineManager(object):

    def __init__(self, size=100):
        self.count = 0
        self.size = size
        self.inited = False

        self._open_array = np.zeros(size)
        self._high_array = np.zeros(size)
        self._low_array = np.zeros(size)
        self._close_array = np.zeros(size)
        self._volume_array = np.zeros(size)
        self._time_deque = deque(maxlen=size)
        self._bar_df = pd.DataFrame(
            0.0,
            index=pd.date_range('2010-01-01', periods=size),
            columns=['open', 'high', 'low', 'close', 'volume']
        )

    def on_bar(self, bar: BarData):
        dt = bar.datetime
        if len(self._time_deque) > 0 and dt <= self._time_deque[-1]:
            return

        self._time_deque.append(dt)

        self._open_array[:-1] = self._open_array[1:]
        self._high_array[:-1] = self._high_array[1:]
        self._low_array[:-1] = self._low_array[1:]
        self._close_array[:-1] = self._close_array[1:]
        self._volume_array[:-1] = self._volume_array[1:]

        self._open_array[-1] = bar.open
        self._high_array[-1] = bar.high
        self._low_array[-1] = bar.low
        self._close_array[-1] = bar.close
        self._volume_array[-1] = bar.volume

        if len(self._time_deque) >= self.size:
            self.inited = True

    @property
    def open(self):
        return self._open_array

    @property
    def high(self):
        return self._high_array

    @property
    def low(self):
        return self._low_array

    @property
    def close(self):
        return self._close_array

    @property
    def volume(self):
        return self._volume_array

    @property
    def time(self):
        return self._time_deque

    def to_df(self):
        if not self.inited:
            raise RuntimeError('kline is not initialed yet')
        self._bar_df['open'] = self.open
        self._bar_df['high'] = self.high
        self._bar_df['low'] = self.low
        self._bar_df['close'] = self.close
        self._bar_df['volume'] = self.volume
        self._bar_df.index = list(self._time_deque)
        return self._bar_df

    def sma(self, n, array=False):
        result = talib.SMA(self.close, n)
        if array:
            return result
        return result[-1]

    def std(self, n, array=False):
        result = talib.STDDEV(self.close, n)
        if array:
            return result
        return result[-1]

    def cci(self, n, array=False):
        result = talib.CCI(self.high, self.low, self.close, n)
        if array:
            return result
        return result[-1]

    def atr(self, n, array=False):
        result = talib.ATR(self.high, self.low, self.close, n)
        if array:
            return result
        return result[-1]

    def rsi(self, n, array=False):
        result = talib.RSI(self.close, n)
        if array:
            return result
        return result[-1]

    def macd(self, fastPeriod, slowPeriod, signalPeriod, array=False):
        macd, signal, hist = talib.MACD(self.close, fastPeriod,
                                        slowPeriod, signalPeriod)
        if array:
            return macd, signal, hist
        return macd[-1], signal[-1], hist[-1]

    def adx(self, n, array=False):
        result = talib.ADX(self.high, self.low, self.close, n)
        if array:
            return result
        return result[-1]

    def boll(self, n, dev, array=False):
        mid = self.sma(n, array)
        std = self.std(n, array)

        up = mid + std * dev
        down = mid - std * dev

        return up, down

    def keltner(self, n, dev, array=False):
        mid = self.sma(n, array)
        atr = self.atr(n, array)

        up = mid + atr * dev
        down = mid - atr * dev

        return up, down

    def donchian(self, n, array=False):
        up = talib.MAX(self.high, n)
        down = talib.MIN(self.low, n)

        if array:
            return up, down
        return up[-1], down[-1]
