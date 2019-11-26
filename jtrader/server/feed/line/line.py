#!/usr/bin/env python
# -*- coding: utf-8 -*-
from jtrader.core.common.template import LazyObject

from collections import deque
import numpy as np
import pandas as pd


class Line(LazyObject):

    def __repr__(self):
        return "%s()" % (
            self.__class__.__name__
        )

    def __init__(self, period=None):
        super(Line, self).__init__()
        self._period = period
        self._values = deque(maxlen=self._period)
        self._times = deque(maxlen=self._period)

    def to_array(self):
        return np.array(self.values)

    def to_series(self):
        return pd.Series(self._values, index=self._times)

    def __len__(self):
        return len(self.values)

    def append(self, item):
        t, v = item
        if len(self._times) and t == self._times[-1]:
            self._times[-1] = t
            self._values[-1] = v
        else:
            self._times.append(t)
            self._values.append(v)
            self.notify()

    @property
    def period(self):
        return self._period

    @property
    def values(self):
        if not self.calculated:
            self.compute()
            return self.values
        else:
            return self._values

    @property
    def times(self):
        if not self.calculated:
            self.compute()
            return self.times
        else:
            return self._times
    
    def clear(self):
        self._times.clear()
        self._values.clear()