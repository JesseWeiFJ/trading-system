#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jtrader.server.feed.indicator.indicator import Indicator
from jtrader.server.feed.line import Line
import numpy as np


class MaxDrawback(Indicator):
    def __init__(self, line: Line, time_window: int, period=10):
        super(MaxDrawback, self).__init__(period)
        self._line = line
        self._time_window = time_window
        self.add_lines([line])

    def __repr__(self):
        return '%s(time_window=%d, line=%s)' % (
            self.__class__.__name__, self._time_window, self._line
        )

    def update(self):
        super(MaxDrawback, self).update()
        self._perform_computations()

    def _perform_computations(self):
        if len(self._line) < self._time_window:
            pass
        else:
            array = self._line.values[-self._time_window:]
            max_array = np.fmax.accumulate(array)
            draw_down = (array - max_array) / max_array
            md = min(draw_down)
            t = self._line.times[-1]
            self.append((t, md))


class MaxGain(MaxDrawback):

    def _perform_computations(self):
        if len(self._line) < self._time_window:
            pass
        else:
            array = self._line.values[-self._time_window:]
            max_array = np.fmax.accumulate(array)
            draw_down = (array - max_array) / max_array
            md = max(draw_down)
            t = self._line.times[-1]
            self.append((t, md))
