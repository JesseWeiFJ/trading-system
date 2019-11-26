#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jtrader.api.ccxt_api import CcxtApi
from jtrader.datatype import *


class BinanceApi(CcxtApi):
    FULL_NAME = 'binance'

    TAG = ExchangeAbbr.BINANCE

    N_RATE_LIMIT = 1200
    PERIOD_LIMIT = '1m'

    N_LIMIT_BAR = 500
    N_LIMIT_ORDER = 500
    N_LIMIT_TRADE = 500

    def create_order(self, order: OrderData, params: dict = None):
        if params is not None:
            params.update({"newClientOrderId": order.client_order_id})
        else:
            params = {"newClientOrderId": order.client_order_id}
        return super(BinanceApi, self).create_order(order, params)
