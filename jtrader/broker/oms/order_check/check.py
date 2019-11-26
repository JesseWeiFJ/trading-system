#!/usr/bin/env python
# -*- coding: utf-8 -*-
from jtrader.datatype import *
from jtrader.datatype.portfolio import Portfolio
from jtrader.core.common import Registered


class OrderCheck(Registered):

    @property
    def portfolio(self):
        return self._portfolio

    @portfolio.setter
    def portfolio(self, value):
        self._portfolio = value

    def __init__(self):
        self._portfolio: Portfolio = None

    def configure(self, risk_config: dict):
        for key, value in risk_config.items():
            setattr(self, key, value)

    def check_order(self, order: OrderData):
        pass
