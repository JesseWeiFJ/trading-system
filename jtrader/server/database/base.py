#!/usr/bin/env python
# -*- coding: utf-8 -*-
from abc import abstractmethod
from jtrader.core.common import Registered


class DatabaseServer(Registered):
    TAG = ''
    @abstractmethod
    def save(self, obj):
        pass

    @abstractmethod
    def configure(self, config):
        pass
