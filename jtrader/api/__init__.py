#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .ccxt_api import CcxtApi
from .binance_api import BinanceApi
from .huobi_api import HuobiApi
from .bitmex_api import BitmexApi
from .okex_api import OKExApi
from .fcoin_api import FCoinApi


class ExchangeApiFactory(object):

    def __new__(cls, tag, api_key="", api_secret="") -> CcxtApi:
        _instance = CcxtApi.factory_create(tag)
        _instance.connect(api_key, api_secret)
        return _instance
