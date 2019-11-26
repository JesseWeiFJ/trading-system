#!/usr/bin/env python
# -*- coding: utf-8 -*-
from jtrader.datatype import *
from jtrader.core.common import Registered, Configurable


class RiskControl(Configurable, Registered):

    def check_risk(self, strategy):
        pass


class RiskControlFactory(object):
    def __new__(cls, name, **kwargs) -> RiskControl:
        _instance = RiskControl.factory_create(name, **kwargs)
        return _instance
