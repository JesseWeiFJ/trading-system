#!/usr/bin/env python
# -*- coding: utf-8 -*-
from jtrader.datatype.base import *
from jtrader.datatype.trades import TradeData, OrderData
from jtrader.datatype.markets import ContractData
from jtrader.core.common.template import Registered


@dataclass()
class PnLData(BaseData):
    strategy_id: str = EMPTY_STRING
    unrealized_pnl: float = EMPTY_FLOAT
    realized_pnl: float = EMPTY_FLOAT
    total_pnl: float = EMPTY_FLOAT
    asset_value: float = EMPTY_FLOAT


@dataclass()
class BalanceData(BaseData):
    strategy_id: str = EMPTY_STRING
    asset: str = EMPTY_STRING
    price: float = 1.0
    total_amount: float = EMPTY_FLOAT
    frozen_amount: float = EMPTY_FLOAT

    def on_market(self, price, dt):
        self.price = price
        self.datetime = dt


@dataclass()
class PositionData(BaseData, Registered):
    TAG = ''

    strategy_id: str = EMPTY_STRING
    symbol: str = EMPTY_STRING
    asset_value: float = EMPTY_FLOAT
    amount: float = EMPTY_FLOAT
    last_price: float = EMPTY_FLOAT
    cost: float = EMPTY_FLOAT
    unrealized_pnl: float = EMPTY_FLOAT
    realized_pnl: float = EMPTY_FLOAT

    @property
    def contract(self):
        return ContractData.get_contract(self.symbol)

    def on_trade(self, trade: TradeData):
        pass

    def on_market(self, price, dt):
        self.last_price = price
        self.datetime = dt
        self.calculate_unrealized_pnl()

    def calculate_unrealized_pnl(self):
        pass

    def unrealized_pnl_rate(self):
        if self.asset_value == 0:
            return 0.0
        else:
            return self.unrealized_pnl / abs(self.asset_value)

    @classmethod
    def frozen_by_order(cls, order: OrderData):
        pass


class PositionFactory(object):
    def __new__(cls, contract_type) -> PositionData:
        _instance = PositionData.factory_create(contract_type)
        return _instance
