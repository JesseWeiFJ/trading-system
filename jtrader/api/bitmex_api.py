#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jtrader.api.ccxt_api import CcxtApi
from jtrader.datatype import *


class BitmexApi(CcxtApi):
    FULL_NAME = 'bitmex'
    TAG = ExchangeAbbr.BITMEX

    N_RATE_LIMIT = 60
    PERIOD_LIMIT = '1m'

    N_LIMIT_BAR = 500
    N_LIMIT_ORDER = 500
    N_LIMIT_TRADE = 500

    STATUS_MAP_REVERSE = dict()
    STATUS_MAP_REVERSE['New'] = EnumOrderStatus.PENDING
    STATUS_MAP_REVERSE['Partially filled'] = EnumOrderStatus.PARTIAL_FILLED
    STATUS_MAP_REVERSE['Filled'] = EnumOrderStatus.FILLED
    STATUS_MAP_REVERSE['Canceled'] = EnumOrderStatus.CANCELLED
    STATUS_MAP_REVERSE['Rejected'] = EnumOrderStatus.ERROR

    def create_order(self, order: OrderData, params:    dict = None):
        if params is not None:
            params.update({"clOrdID": order.client_order_id})
        else:
            params = {"clOrdID": order.client_order_id}
        return super(BitmexApi, self).create_order(order, params)

    @staticmethod
    def _get_precision(number):
        return number

