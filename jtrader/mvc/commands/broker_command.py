#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jtrader.datatype import *
from jtrader.mvc.commands.command import CommandBaseData
from jtrader.broker import Broker as _Actor
from jtrader.datatype.markets import ContractData


ALL_GATEWAY = 'ALL'


@dataclass
class BrokerCommand(CommandBaseData):
    ACTOR = _Actor.__name__


@dataclass
class ShowBalanceCommand(BrokerCommand):
    gateway_name: str = EMPTY_STRING
    currency: str = 'USDT'

    def parse(self, cmd_str: str):
        command_args = self.split(cmd_str)
        self.gateway_name = command_args[0].upper()
        if len(command_args) > 1:
            self.currency = command_args[1].upper()

    def execute(self, actor: _Actor):
        balance_df = actor.query_balance(exchange=self.gateway_name)
        balance_df['price'] = 1.0
        balance_df['notional'] = 0.0
        balance_df['symbol'] = ''
        depth_df = actor.query_data('depth').set_index('symbol')

        for asset in balance_df.index:
            if asset == self.currency:
                continue
            symbol = asset + '/' + self.currency + '.' + self.gateway_name
            if symbol in depth_df.index:
                price = depth_df.loc[symbol]['bid_prices'][0]
                balance_df.loc[asset, 'symbol'] = symbol
                balance_df.loc[asset, 'price'] = price
            else:
                continue
        balance_df['notional'] = balance_df['price'] * balance_df['total_amount']
        balance_str = "Balance of {gateway}: \n{balance}".format(
            gateway=self.gateway_name, balance=balance_df.to_string()
        )
        self.render(balance_str)
        return balance_df


@dataclass
class QueryCommand(BrokerCommand):
    name: str = EMPTY_STRING
    query: str = EMPTY_STRING
    columns: list = field(default_factory=list)

    def parse(self, cmd_str: str):
        command_args = self.split(cmd_str)
        self.name = command_args[0]
        if len(command_args) > 1:
            self.query = command_args[1]
            self.columns = command_args[2:]

    def execute(self, actor: _Actor):
        print('')
        print(actor.query_data(self.name, self.query, self.columns).to_string())


class CloseOpenPositionCommand(ShowBalanceCommand):

    def execute(self, actor: _Actor):
        balance_df = super(CloseOpenPositionCommand, self).execute(actor)
        for asset in balance_df.index:
            position = balance_df.loc[asset]
            symbol = position['symbol']
            if symbol:
                price = position['price']
                contract = ContractData.get_contract(symbol)
                if position['total_amount'] > contract.min_quantity and \
                        position['notional'] > contract.min_notional:
                    self.render(f'handling position {asset}...')

                    if position['frozen_amount'] > 0:
                        pass

                    order = OrderData()
                    order.symbol = symbol
                    order.direction = EnumOrderDirection.SELL
                    order.price = price
                    order.volume = position['total_amount']
                    order.strategy_id = 'manual'
                    actor.send_order(order)
                # else:
                #     self.render(f'Balance not enough to close: {position}')
