#!/usr/bin/env python
# -*- coding: utf-8 -*-
from jtrader.server.database.base import DatabaseServer


class MockDBServer(DatabaseServer):
    TAG = 'mock'

    def save(self, obj):
        pass

    def configure(self, config):
        pass
