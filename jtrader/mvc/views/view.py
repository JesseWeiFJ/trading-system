#!/usr/bin/env python
# -*- coding: utf-8 -*-
from jtrader.core.common import Registered


class Viewer(Registered):
    def render(self, msg):
        pass


class ViewerFactory(object):
    def __new__(cls, contract_type) -> Viewer:
        _instance = Viewer.factory_create(contract_type)
        return _instance
