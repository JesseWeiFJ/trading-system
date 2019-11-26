#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import time
from jtrader.api.ccxt_api import CcxtApi
from jtrader.datatype import *


class FCoinApi(CcxtApi):
    FULL_NAME = 'fcoin'
    TAG = ExchangeAbbr.FCOIN

    N_RATE_LIMIT = 100
    PERIOD_LIMIT = '10s'

    N_LIMIT_BAR = 2000
    N_LIMIT_ORDER = 100
    N_LIMIT_TRADE = 100

    def connect(self, api_key='', api_secret=''):
        super(FCoinApi, self).connect(api_key, api_secret)
        self._exchange.enableRateLimit = True

    def fetch_order_trades(self, order: OrderData):
        if not order.order_id:
            return []
        result = self.exchange.private_get_orders_order_id_match_results({'order_id': order.order_id})
        trade_list = []
        for idx, data in enumerate(result['data']):
            trade = TradeData()
            trade.symbol = order.symbol
            trade.client_order_id = order.client_order_id
            trade.strategy_id = order.strategy_id
            trade.order_id = order.order_id
            trade.trade_id = '__'.join((order.order_id, str(idx)))
            trade.volume = float(data['filled_amount'])
            trade.price = float(data['price'])
            trade.direction = order.direction

            quote = self.contracts[order.symbol].asset_quote
            base = self.contracts[order.symbol].asset_base

            fee = float(data['fill_fees'])
            if fee == 0:
                # maker
                fee = -float(data['fees_income'])
                if trade.direction == EnumOrderDirection.BUY:
                    fee_asset = quote
                else:
                    fee_asset = base
            else:
                # taker
                if trade.direction == EnumOrderDirection.BUY:
                    fee_asset = base
                else:
                    fee_asset = quote

            trade.commission = fee
            trade.commission_asset = fee_asset
            trade.datetime = datetime.datetime.utcfromtimestamp(data['created_at'] / 1000.0)
            trade_list.append(trade)
        return trade_list

    def on_order(self, order: OrderData):
        # if order was executed at once, then no need to add into local oms
        # trading ws only fetch pending order status
        if order.is_closed():
            self._local_order_manager.pop(order.client_order_id)
            trade_list = self.fetch_order_trades(order)
            notional = 0.0
            for trade in trade_list:
                notional += trade.price * trade.volume
                self.on_trade(trade)
            order.executed_notional = notional
        else:
            self._local_order_manager.on_order(order)
        self._callback(order)

    def cancel_order(self, order_cancel: OrderData):
        super(FCoinApi, self).cancel_order(order_cancel)
