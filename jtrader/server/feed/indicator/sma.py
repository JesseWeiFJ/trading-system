#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jtrader.server.feed.indicator.indicator import Indicator
from jtrader.server.feed.line import Line
import numpy as np


class SMA(Indicator):
    def __init__(self, line: Line, time_window: int, period=10):
        super(SMA, self).__init__(period)
        self._line = line
        self._time_window = time_window
        self.add_lines([line])

    def __repr__(self):
        return '%s(time_window=%d, line=%s)' % (
            self.__class__.__name__, self._time_window, self._line
        )

    def update(self):
        super(SMA, self).update()
        self._perform_computations()

    def _perform_computations(self):
        if len(self._line) < self._time_window:
            pass
        else:
            ma = np.mean(list(self._line.values)[-self._time_window:])
            t = self._line.times[-1]
            self.append((t, ma))
