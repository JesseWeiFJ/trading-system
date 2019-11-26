#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import json
import zlib
import copy
import datetime
from abc import abstractmethod
import typing
from jtrader.core.common import logger, Registered
from jtrader.datatype import *
from jtrader.core.tools.client import WebsocketClient
from jtrader.api import CcxtApi


class WebsocketBaseApi(WebsocketClient):
    HOST = ''

    @property
    def api(self):
        return self._api

    def __init__(self, api):
        super(WebsocketBaseApi, self).__init__()
        self._api: CcxtApi = api


class MarketWebsocketApi(WebsocketBaseApi):
    N_BACK_FILL = 100

    def __init__(self, api):
        """"""
        super().__init__(api)
        self._callback_dict = {}
        self._bar_dict: typing.Dict[typing.Tuple[str, str], BarData] = {}
        self._depth_dict: typing.Dict[str, DepthData] = {}

        self._symbol_list = []
        self._frequency_list = []
        self._depth_flag = False

    def init(self, symbol_list, frequency_list, depth_flag=False):
        self._symbol_list = symbol_list
        self._frequency_list = frequency_list
        self._depth_flag = depth_flag

    def back_fill(self):
        for frequency in self._frequency_list:
            bar_list = self.api.back_fill_bars(self._symbol_list, self.N_BACK_FILL, frequency)
            for bar in bar_list:
                self.api.on_bar(bar)

    def on_connected(self):
        super(MarketWebsocketApi, self).on_connected()
        for symbol in self._symbol_list:
            if self._depth_flag:
                self.subscribe_depth(symbol)
            for frequency in self._frequency_list:
                self.subscribe_bar(symbol, frequency)

    def _parse_depth(self, packet, depth: DepthData):
        pass

    def _parse_bar(self, packet, bar: BarData):
        pass

    @staticmethod
    def round_dt(dt: datetime.datetime, freq: str):
        interval = TIME_INTERVAL_MAP[freq].total_seconds()
        round_dt = datetime.datetime.fromtimestamp(int(dt.timestamp() / interval) * interval)
        return round_dt # - TIME_INTERVAL_MAP[freq]

    def _on_bar_impl(self, symbol, frequency):
        bar = BarData()
        bar.symbol = symbol
        bar.frequency = frequency
        bar.datetime = self.round_dt(datetime.datetime.utcnow(), frequency)
        self._bar_dict[(symbol, frequency)] = bar

        def callback(bar_data):
            origin_dt = bar.datetime
            self._parse_bar(bar_data, bar)
            if bar.datetime > origin_dt:
                self.api.on_bar(copy.copy(bar))

        return callback

    def _on_depth_impl(self, symbol):
        depth = DepthData()
        depth.symbol = symbol
        self._depth_dict[symbol] = depth

        def callback(depth_data):
            self._parse_depth(depth_data, depth)
            self.api.on_depth(copy.copy(depth))

        return callback

    @abstractmethod
    def subscribe_bar(self, symbol, frequency):
        pass

    @abstractmethod
    def subscribe_depth(self, symbol):
        pass

    def start(self):
        self.back_fill()
        super(MarketWebsocketApi, self).start()


class TradeWebsocketApi(WebsocketBaseApi):
    def on_connected(self):
        if self.api.api_key and self.api.api_secret:
            self.subscribe_user_stream()
        super(TradeWebsocketApi, self).on_connected()

    @abstractmethod
    def subscribe_user_stream(self):
        pass


class AggregateWebsocketApi(TradeWebsocketApi, MarketWebsocketApi):
    pass
