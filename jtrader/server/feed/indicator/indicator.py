#!/usr/bin/env python
# -*- coding: utf-8 -*-
from jtrader.server.feed.line import Line


class Indicator(Line):

    def __init__(self, period):
        super(Indicator, self).__init__(period)
        self._lines = []

    def get_feed_lines(self):
        lines = []
        for line in self._lines:
            if isinstance(line, Indicator):
                lines.extend(line.get_feed_lines())
            else:
                lines.append(line)
        return lines

    def add_lines(self, lines):
        for line in lines:
            if line not in self._lines:
                self._lines.append(line)
                line.register(self)

    def _perform_computations(self):
        raise NotImplementedError('Please implement method _perform_computations')

    def compute(self):
        if not self.calculated:
            for line in self._lines:
                line.compute()
        super(Indicator, self).compute()
