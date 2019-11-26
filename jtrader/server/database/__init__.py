#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .base import DatabaseServer
from .mongo import MongoSerevr
from .mock import MockDBServer


class DBServerFactory(object):
    def __new__(cls, name, config=None) -> DatabaseServer:
        _instance: DatabaseServer = DatabaseServer.factory_create(name)
        if config:
            _instance.configure(config)
        return _instance
