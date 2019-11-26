#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as _pd
import sys

DEFAULT_START_TIME = _pd.datetime(1970, 1, 1)
EPSILON = sys.float_info.epsilon * 2**4

TIME_INTERVAL_MAP = {
    frequency: _pd.to_timedelta(frequency) for frequency in
    ['1s', '15s', '1m', '5m', '10m', '15m', '20m', '30m', '45m',
     '1h', '2h', '3h', '4h', '1d']
}


class ContractTypeAbbr(object):
    SWAP = 'swap'
    SPOT = 'spot'
    FUTURES = 'futures'


class ExchangeAbbr(object):
    BINANCE = 'BNC'
    HUOBI = 'HB'
    HBDM = 'HBDM'
    BITMEX = 'BTX'
    OKEX = 'OKX'
    FCOIN = 'FC'
    COINMARKETMAP = 'CCM'
    SIMULATE = 'SIMU'
