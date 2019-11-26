#!/usr/bin/env python
# -*- coding: utf-8 -*-
from jtrader.core.common import logger, LimitedQueryContext, Registered
from jtrader.datatype import *

from ccxt.base.exchange import Exchange
import ccxt
import ccxt.base.errors

import calendar
import typing
import numpy as np
import pandas as pd
import copy
import datetime
import requests
from threading import Lock


class LocalOrderManager(object):
    def __init__(self):
        self._order_dict: typing.Dict[str, OrderData] = {}
        self._lock = Lock()

    def pop(self, cli_id):
        if cli_id in self._order_dict:
            with self._lock:
                if cli_id in self._order_dict:
                    self._order_dict.pop(cli_id)

    def on_order(self, order: OrderData):
        cli_id = order.client_order_id
        with self._lock:
            if cli_id in self._order_dict:
                self._order_dict[cli_id].on_order(order)
            else:
                self._order_dict[cli_id] = order

    def clone(self, cli_id):
        if cli_id in self._order_dict:
            with self._lock:
                if cli_id in self._order_dict:
                    return self._order_dict[cli_id].copy()

    def purge(self):
        with self._lock:
            pop_ids = []
            for cli_id, order in self._order_dict.items():
                if order.is_closed():
                    pop_ids.append(pop_ids)
            for cli_id in pop_ids:
                self._order_dict.pop(cli_id)

    def __iter__(self):
        return iter(list(self._order_dict.values()))

    def __getitem__(self, item):
        return self._order_dict[item]

    def __contains__(self, item):
        return item in self._order_dict


class CcxtApi(Registered):
    FULL_NAME = ''

    STATUS_MAP_REVERSE = dict()
    STATUS_MAP_REVERSE['open'] = EnumOrderStatus.PENDING
    STATUS_MAP_REVERSE['closed'] = EnumOrderStatus.FILLED
    STATUS_MAP_REVERSE['canceled'] = EnumOrderStatus.CANCELLED

    DIRECTION_MAP = dict()
    DIRECTION_MAP[EnumOrderDirection.BUY] = 'buy'
    DIRECTION_MAP[EnumOrderDirection.SELL] = 'sell'
    DIRECTION_MAP_RESERVE = {v: k for k, v in DIRECTION_MAP.items()}

    ORDER_TYPE_MAP = dict()
    ORDER_TYPE_MAP[EnumOrderType.MARKET] = 'market'
    ORDER_TYPE_MAP[EnumOrderType.LIMIT] = 'limit'
    ORDER_TYPE_MAP_REVERSE = {v: k for k, v in ORDER_TYPE_MAP.items()}

    TAG = ''

    N_RATE_LIMIT = 300
    PERIOD_LIMIT = '1m'

    N_LIMIT_ORDER = 300
    N_LIMIT_TRADE = 300

    N_LIMIT_BAR = 500
    N_LIMIT_MARKET_TRADE = 300

    @property
    def contracts(self):
        return self._contracts

    @property
    def exchange(self):
        return self._exchange

    @property
    def oms(self):
        return self._local_order_manager

    def __init__(self):
        super(CcxtApi, self).__init__()
        self.api_key = ""
        self.api_secret = ""

        self.exchange_symbol_dict = {}
        self._contracts: typing.Dict[str, ContractData] = {}
        self._root_symbol_dict = {}
        self._exchange = Exchange()
        self._limit_context = LimitedQueryContext(self.N_RATE_LIMIT, self.PERIOD_LIMIT)
        self._local_order_manager = LocalOrderManager()

        self._callback: typing.Callable = print

    def set_callback(self, callback):
        self._callback = callback

    def throttle(self):
        with self._limit_context:
            pass

    def on_order(self, order: OrderData):
        self._local_order_manager.on_order(order)
        self._callback(order)

    def on_trade(self, trade: TradeData):
        self._callback(trade)

    def on_bar(self, bar: BarData):
        self._callback(bar)

    def on_depth(self, depth: DepthData):
        self._callback(depth)

    def connect(self, api_key='', api_secret=''):
        self.api_key = api_key
        self.api_secret = api_secret
        config = {
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': False,
        }
        exchange = self.FULL_NAME
        api_class = getattr(ccxt, exchange)
        self._exchange = api_class(config)
        self.fetch_contract()

        for symbol, contract in self.contracts.items():
            exchange_symbol = contract.symbol_exchange
            self.exchange_symbol_dict[exchange_symbol] = symbol

    # --------------------- trading interface ---------------------
    def create_order(self, order: OrderData, params: dict = None):
        self.throttle()
        self._local_order_manager.on_order(order)

        order = copy.copy(order)
        contract = self._contracts[order.symbol]
        symbol_root = contract.symbol_root
        if params is None:
            params = {}
        try:
            price = order.price
            if order.order_type == EnumOrderType.MARKET:
                price = None

            logger.debug('%s sending order %s', self, order.client_order_id)
            data = self._exchange.create_order(symbol_root,
                                               self.ORDER_TYPE_MAP[order.order_type],
                                               self.DIRECTION_MAP[order.direction],
                                               order.volume,
                                               price,
                                               params)
            if 'status' in data:
                status = self.STATUS_MAP_REVERSE[data['status']]
            else:
                status = EnumOrderStatus.PENDING
            order.status = status
            order.order_id = data['id']
            logger.debug('%s sent order %s successfully with order id %s and status %s ', self, order.client_order_id,
                         order.order_id, order.status)

        except ccxt.InsufficientFunds as e:
            order.status = EnumOrderStatus.REJECTED
            balance_df = self.fetch_balance()
            base_amount = balance_df.loc[contract.symbol_base]
            quote_amount = balance_df.loc[contract.symbol_quote]
            logger.warn(
                "Insufficient balance for order: %s\n%s\n%s", e.args, order,
                f'There was only {contract.symbol_base} \n'
                f'{base_amount}  \n'
                f'and {quote_amount} \n'
                f'{contract.symbol_quote} \n'
                f'in the balance. '
            )
        except ccxt.InvalidOrder as e:
            order.status = EnumOrderStatus.REJECTED
            logger.warn("InvalidOrder error: %s\n%s", e.args, order)
        except ccxt.ExchangeError as e:
            logger.warn("Exchange error: %s\n%s", e.args, order)
            order.status = EnumOrderStatus.REJECTED
        except ccxt.NetworkError as e:
            logger.warn("Network error: %s\n%s", e.args, order)
            order.status = EnumOrderStatus.ERROR
        except requests.HTTPError as e:
            logger.warn("Http error: %s\n%s", e.args, order)
            order.status = EnumOrderStatus.ERROR

        self._local_order_manager.on_order(order)
        self.on_order(order)
        return order

    def cancel_order(self, order_cancel: OrderData):
        self.throttle()
        self._local_order_manager.on_order(order_cancel)

        order_id = order_cancel.order_id
        contract = self._contracts[order_cancel.symbol]
        symbol_root = contract.symbol_root
        logger.debug('%s cancel order %s', self, order_cancel.client_order_id)
        try:
            self._exchange.cancel_order(order_id, symbol_root)
            logger.debug('%s canceled order %s successfully', self, order_cancel.client_order_id)
            order_cancel.status = EnumOrderStatus.CANCELLED
        except ccxt.errors.OrderNotFound as e:
            logger.info("Order already been closed or cancelled before: %s\n%s", e.args, order_cancel)
            order_status = self.fetch_order_status(order_cancel)
            order_cancel.on_order(order_status)
        except ccxt.errors.NetworkError as e:
            logger.info("Network error: %s\n%s", e.args, order_cancel)
            order_cancel.status = EnumOrderStatus.CANCEL_ERROR

        self._local_order_manager.on_order(order_cancel)
        self.on_order(order_cancel)
        return order_cancel

    def fetch_order_status(self, order: OrderData):
        self.throttle()
        logger.debug('fetch status for order %s', order)
        symbol = order.symbol
        symbol_root = self.contracts[symbol].symbol_root
        order_id = order.order_id
        data = self._exchange.fetch_order(order_id, symbol_root)
        order_status = copy.copy(order)

        order_status.status = self.STATUS_MAP_REVERSE[data['status']]
        order_status.executed_volume = data['filled']

        return order_status

    def fetch_order_trades(self, order: OrderData) -> typing.List[TradeData]:
        symbol_root = self.contracts[order.symbol].symbol_root
        result = self._exchange.fetch_order_trades(order.order_id, symbol_root)
        trade_list = []
        for data in result:
            trade = self._parse_trade(data)
            trade.strategy_id = order.strategy_id
            trade.client_order_id = order.client_order_id
            trade_list.append(trade)
        return trade_list

    def _parse_trade(self, data):
        trade = TradeData()
        trade.symbol = self._root_symbol_dict[data['symbol']]
        trade.order_id = data['order']
        trade.trade_id = data['id']
        trade.volume = data['amount']
        trade.price = data['price']
        trade.direction = self.DIRECTION_MAP_RESERVE[data['side']]
        trade.commission = data['fee']['cost']
        trade.commission_asset = '.'.join([data['fee']['currency'], self.TAG])
        trade.datetime = datetime.datetime.utcfromtimestamp(data['timestamp'] / 1000.0)
        return trade

    def fetch_my_trades(self, symbol, since=DEFAULT_START_TIME, params=None):
        self.throttle()
        if params is None:
            params = {}
        if symbol is None:
            symbol_root = None
        else:
            symbol_root = self.contracts[symbol].symbol_root
        start_timestamp = int(calendar.timegm(since.timetuple()) * 1000)
        data_list = self._exchange.fetch_my_trades(symbol_root, since=start_timestamp, params=params)

        trade_list = []
        for data in data_list:
            trade_list.append(self._parse_trade(data))

        return trade_list

    def _fetch_order_impl(self, function, symbol, since, params):
        self.throttle()
        if symbol is None:
            symbol_root = None
        else:
            symbol_root = self.contracts[symbol].symbol_root
        if params is None:
            params = {}

        data_list = []
        start_timestamp = int(calendar.timegm(since.timetuple()) * 1000)
        limit = self.N_LIMIT_ORDER
        while True:
            orders = function(symbol_root, since=start_timestamp, limit=limit, params=params)
            if orders is None:
                break
            if len(orders):
                data_list.extend(orders)
            if len(orders) == limit:
                start_timestamp = orders[-1]['timestamp']
            else:
                break

        order_list = []
        order_id_set = set()
        for data in data_list:
            order_id = data['id']
            if order_id not in order_id_set:
                order_id_set.add(order_id)

                order = OrderData()
                order.order_id = order_id
                order.symbol = self._root_symbol_dict[data['symbol']]
                order.datetime = datetime.datetime.utcfromtimestamp(data['timestamp'] / 1000.0)
                order.volume = data['amount']
                order.executed_volume = data['filled']
                order.executed_notional = data['cost']
                order.price = data['price']

                order.status = self.STATUS_MAP_REVERSE[data['status']]
                order.direction = self.DIRECTION_MAP_RESERVE[data['side']]
                order.order_type = self.ORDER_TYPE_MAP_REVERSE[data['type']]

                order_list.append(order)

        return order_list

    def fetch_open_orders(self, symbol, since=DEFAULT_START_TIME, params=None):
        return self._fetch_order_impl(self._exchange.fetch_open_orders, symbol, since, params)

    def fetch_close_orders(self, symbol, since=DEFAULT_START_TIME, params=None):
        return self._fetch_order_impl(self._exchange.fetch_closed_orders, symbol, since, params)

    def fetch_orders(self, symbol, since=DEFAULT_START_TIME, params=None):
        return self._fetch_order_impl(self._exchange.fetch_orders, symbol, since, params)

    def fetch_balance(self):
        self.throttle()
        try:
            # noinspection PyUnresolvedReferences
            data = self._exchange.fetch_balance()
        except ccxt.base.errors.AuthenticationError:
            return pd.DataFrame()
        account_df = pd.DataFrame([data['free'], data['used'], data['total']],
                                  index=['free_amount', 'frozen_amount', 'total_amount']).T
        index = account_df.any(axis=1)
        account_df = account_df[index]

        return account_df

    # --------------------- market data ---------------------

    def fetch_ticker(self, symbol):
        symbol_root = self.contracts[symbol].symbol_root
        ticker = self._exchange.fetch_ticker(symbol_root)
        ticker.pop('info')
        return ticker

    def fetch_bars(self, symbol, freq, start_date, end_date=None, return_df=False):
        symbol_root = self.contracts[symbol].symbol_root
        if end_date is None:
            now = datetime.datetime.utcnow()
            end_date = start_date + TIME_INTERVAL_MAP[freq] * (self.N_LIMIT_BAR - 1)
            end_date = min(end_date, now - TIME_INTERVAL_MAP[freq])
        start_timestamp = int(calendar.timegm(start_date.timetuple()) * 1000)
        end_timestamp = int(calendar.timegm(end_date.timetuple()) * 1000)
        time_delta = int(TIME_INTERVAL_MAP[freq].total_seconds() * 1000)

        ohlcv_list = []
        while start_timestamp <= end_timestamp:
            self.throttle()
            ohlcv = self._exchange.fetch_ohlcv(symbol_root, freq, start_timestamp, self.N_LIMIT_BAR)
            if ohlcv is not None and len(ohlcv):
                ohlcv_list.extend(ohlcv)
                actual_last_timestamp = ohlcv[-1][0]
                logger.debug('download {symbol}:{freq} from [{start} ~~ {end}]'.format(
                    symbol=symbol,
                    freq=freq,
                    start=datetime.datetime.fromtimestamp(start_timestamp / 1000),
                    end=datetime.datetime.fromtimestamp(actual_last_timestamp / 1000),
                ))
                expect_last_timestamp = start_timestamp + (self.N_LIMIT_BAR - 1) * time_delta
                next_timestamp = max(actual_last_timestamp, expect_last_timestamp) + time_delta
                start_timestamp = next_timestamp
            else:
                break

        # transform into data frame:
        #   1. check data duplication
        #   2. constrain data in giver date range
        #   3. timestamp -> datetime
        bar_df = pd.DataFrame(ohlcv_list, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])

        bar_list = []
        if len(bar_df):
            non_duplicate_index = ~bar_df['datetime'].duplicated()
            date_range_index = bar_df['datetime'] <= end_timestamp
            filter_index = non_duplicate_index & date_range_index

            bar_df = bar_df[filter_index]
            bar_df['datetime'] = pd.to_datetime(bar_df['datetime'], unit='ms')
            bar_df['frequency'] = freq
            bar_df['symbol'] = symbol

            if return_df:
                return bar_df

            ohlcv_records = bar_df.to_dict('records')
            for record in ohlcv_records:
                bar = BarData.from_dict(record)
                bar_list.append(bar)
        return bar_list

    def first_valid_date(self, symbol):
        self.throttle()
        symbol_root = self.contracts[symbol].symbol_root
        start_date = DEFAULT_START_TIME
        freq = '1d'
        start_timestamp = int(calendar.timegm(start_date.timetuple()) * 1000)
        ohlcv = self._exchange.fetch_ohlcv(symbol_root, freq, start_timestamp, 5)
        if len(ohlcv):
            return datetime.datetime.utcfromtimestamp(ohlcv[0][0] / 1000.0)
        else:
            return start_date

    def back_fill_bars(self, symbols, periods=50, freq='1m'):
        bar_list = []
        end_date = datetime.datetime.utcnow() - TIME_INTERVAL_MAP[freq]
        start_date = end_date - TIME_INTERVAL_MAP[freq] * periods
        for symbol in symbols:
            bars = self.fetch_bars(symbol, freq, start_date, end_date)
            bar_list.extend(bars)
        return bar_list

    def fetch_depth(self, symbol):
        self.throttle()
        symbol_root = self.contracts[symbol].symbol_root
        data = self._exchange.fetch_l2_order_book(symbol_root)
        depth = DepthData()
        depth.symbol = symbol
        for n, bid in enumerate(data['bids'][:DepthData.N_DEPTH]):
            depth.bid_prices[n] = bid[0]
            depth.bid_volumes[n] = bid[1]

        for n, ask in enumerate(data['asks'][:DepthData.N_DEPTH]):
            depth.ask_prices[n] = ask[0]
            depth.ask_volumes[n] = ask[1]

        if data['timestamp']:
            depth.datetime = datetime.datetime.utcfromtimestamp(data['timestamp'] / 1000)
        else:
            depth.datetime = datetime.datetime.utcnow()
        return depth

    # --------------------- contract information ---------------------
    def fetch_contract(self, return_df=False):
        # codes are removed
        pass

    @staticmethod
    def _get_precision(number):
        return np.float_power(10, -number)
