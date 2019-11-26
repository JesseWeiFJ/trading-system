#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import OrderedDict
import typing

from jtrader.core.common import logger
from jtrader.datatype.trades import OrderData, TradeData, FundingData
from jtrader.datatype.markets import ContractData, DepthData, BarData
from jtrader.datatype.positions import PositionData, PositionFactory, PnLData, BalanceData
from jtrader.datatype.enums import *


class Portfolio(object):

    def __init__(self, strategy_id='', accounting_unit='USD'):
        self._strategy_id = strategy_id
        self._accounting_unit = accounting_unit

        self._order_frozen_dict: typing.Dict[str, float] = {}
        self._position_dict: typing.Dict[str, PositionData] = OrderedDict()
        self._balance_dict: typing.Dict[str, BalanceData] = OrderedDict()

    def __repr__(self):
        return '%s(%s)' % (
            self.__class__.__name__, self._strategy_id
        )

    @property
    def balances(self):
        return self._balance_dict

    @property
    def positions(self):
        return self._position_dict

    def _get_balance(self, asset):
        if asset not in self._balance_dict:
            balance = BalanceData()
            balance.strategy_id = self._strategy_id
            balance.asset = asset
            self._balance_dict[asset] = balance
        return self._balance_dict[asset]

    def _get_position(self, symbol):
        if symbol not in self._position_dict:
            contract = ContractData.get_contract(symbol)
            position = PositionFactory(contract.contract_type)
            position.symbol = symbol
            position.strategy_id = self._strategy_id
            position.asset_base = contract.asset_base
            position.asset_quote = contract.asset_quote
            self._position_dict[symbol] = position
        return self._position_dict[symbol]

    def __contains__(self, item):
        return item in self._position_dict

    def __getitem__(self, item):
        return self._get_position(item)

    def __iter__(self):
        return iter(self._position_dict.values())

    def _available_balance(self, asset):
        balance = self._get_balance(asset)
        return balance.total_amount - balance.frozen_amount

    def available_base_amount(self, symbol):
        base_symbol = ContractData.get_contract(symbol).asset_base
        return self._available_balance(base_symbol)

    def available_quote_amount(self, symbol):
        quote_symbol = ContractData.get_contract(symbol).asset_quote
        return self._available_balance(quote_symbol)

    def adjust_asset(self, asset, volume):
        balance = self._get_balance(asset)
        balance.total_amount += volume
        logger.info('%s processed asset %s %s\n'
                    'Present positions is:\n%s',
                    self, asset, volume, balance.total_amount)

    def _update_price(self, symbol, price, dt):
        position = self._get_position(symbol)
        position.on_market(price, dt)
        contract = position.contract
        if contract.asset_quote == self._accounting_unit:
            balance = self._get_balance(contract.asset_base)
            balance.on_market(price, dt)

    def on_order_status(self, order: OrderData):
        client_order_id = order.client_order_id
        if order.is_closed():
            if client_order_id in self._order_frozen_dict:
                asset, amount = self._order_frozen_dict[client_order_id]
                balance = self._get_balance(asset)
                balance.frozen_amount -= amount
                del self._order_frozen_dict[client_order_id]
                logger.debug('%s unfreeze %.6f amount of %s by order %s', self, amount, asset, order.client_order_id)
        else:
            if client_order_id not in self._order_frozen_dict:
                symbol = order.symbol
                order_type = order.order_type
                if order_type in ORIGIN_ORDER_TYPES:
                    asset, amount = self._get_position(symbol).frozen_by_order(order)
                    balance = self._get_balance(asset)
                    balance.frozen_amount += amount
                    self._order_frozen_dict[order.client_order_id] = (asset, amount)
                    logger.debug('%s freeze %.6f amount of %s by order %s', self, amount, asset, order.client_order_id)

    def on_trade(self, trade: TradeData):
        symbol = trade.symbol
        contract = trade.contract
        position = self._get_position(symbol)

        # base_change, quote_change = position.quantity_change(trade)
        # base_change, quote_change = position.on_transaction(base_change, quote_change)

        base_change, quote_change = position.on_trade(trade)

        self.adjust_asset(contract.asset_base, base_change)
        self.adjust_asset(contract.asset_quote, quote_change)

        self._update_price(symbol, trade.price, trade.datetime)

    def on_bar(self, bar: BarData):
        symbol = bar.symbol
        if symbol in self._position_dict:
            dt = bar.settle_time()
            price = bar.close
            self._update_price(symbol, price, dt)

    def on_depth(self, depth: DepthData):
        symbol = depth.symbol
        if symbol in self._position_dict:
            dt = depth.datetime
            # price = (depth.bid_prices[0] + depth.ask_prices[0]) * 0.5
            price = depth.bid_prices[0]
            self._update_price(symbol, price, dt)

    def on_funding(self, funding: FundingData):
        asset = funding.symbol
        volume = funding.volume
        self.adjust_asset(asset, volume)

    def get_cash_value(self):
        cash_value = 0.0
        for key, value in self._balance_dict.items():
            if key.__contains__(self._accounting_unit):
                cash_value += value.total_amount
        return cash_value

    @property
    def pnl(self):
        position_df = PositionData.to_df(self._position_dict.values())
        balance_df = BalanceData.to_df(self._balance_dict.values())

        pnl = PnLData()
        pnl.strategy_id = self._strategy_id
        if len(position_df):
            pnl.realized_pnl = position_df['realized_pnl'].sum()
            pnl.unrealized_pnl = position_df['unrealized_pnl'].sum()
            pnl.total_pnl = pnl.realized_pnl + pnl.unrealized_pnl
        if len(balance_df):
            balance_df['notional'] = balance_df['price'] * balance_df['total_amount']
            pnl.asset_value = balance_df['notional'].sum()
        return pnl

    def describe(self):
        position_df = PositionData.to_df(self._position_dict.values())
        if len(position_df):
            position_df.set_index(position_df['symbol'], inplace=True)
            position_df = position_df.drop(['datetime', 'strategy_id'], axis=1)
            contract_position_str = position_df.to_string()
        else:
            contract_position_str = '[]'

        balance_df = BalanceData.to_df(self._balance_dict.values())
        if len(balance_df):
            balance_df = balance_df.set_index('asset')
            # balance_df['notional'] = balance_df['price'] * balance_df['total_amount']
            # balance_df = balance_df.reindex(['notional', 'total_amount', 'frozen_amount', 'price'], axis=1)
            balance_df = balance_df.reindex(['total_amount', 'frozen_amount', 'price'], axis=1)
            balance_str = balance_df.to_string()
        else:
            balance_str = '[]'

        return "Positions: \n%s\n" \
               "Assets: \n%s\n" \
               "Total pnl: \n%s\n" \
               % (
                   contract_position_str, balance_str, self.pnl.total_pnl
               )

