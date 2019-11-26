#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jtrader.api.ccxt_api import CcxtApi
from jtrader.datatype.constants import ExchangeAbbr


class HuobiApi(CcxtApi):
    FULL_NAME = 'huobipro'
    TAG = ExchangeAbbr.HUOBI

    N_RATE_LIMIT = 100
    PERIOD_LIMIT = '10s'

    N_LIMIT_BAR = 2000
    N_LIMIT_ORDER = 100
    N_LIMIT_TRADE = 100
