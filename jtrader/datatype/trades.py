#!/usr/bin/env python
# -*- coding: utf-8 -*-
import typing
import uuid
import pandas as pd
from jtrader.core.common import logger
from jtrader.datatype.base import *
from jtrader.datatype.enums import *
from jtrader.datatype.markets import ContractData


def generate_id():
    return str(uuid.uuid1().hex)


@dataclass()
class TradingBaseData(BaseData):
    strategy_id: str = EMPTY_STRING
    symbol: str = EMPTY_STRING

    COLUMN_ENUM = []

    @property
    def contract(self):
        return ContractData.get_contract(self.symbol)

    def to_dict(self, dict_factory: typing.Type[dict] = dict):
        result = super(TradingBaseData, self).to_dict(dict_factory)
        for column in self.COLUMN_ENUM:
            result[column] = result[column].name
        return result


@dataclass()
class OrderData(TradingBaseData):
    EVENT_TYPE = EnumEventType.ORDER
    COLUMN_ENUM = ['direction', 'order_type', 'status']

    price: float = EMPTY_FLOAT
    volume: float = EMPTY_FLOAT
    executed_volume: float = EMPTY_FLOAT
    executed_notional: float = EMPTY_FLOAT

    direction: EnumOrderDirection = EnumOrderDirection.BUY
    # offset: EnumOffSet = EnumOffSet.OPEN
    order_type: EnumOrderType = EnumOrderType.LIMIT
    status: EnumOrderStatus = EnumOrderStatus.NEW

    client_order_id: str = field(default_factory=generate_id)
    order_id: str = EMPTY_STRING

    parameter: dict = field(default_factory=dict)

    def is_closed(self):
        return self.status in FINISHED_STATUS_SET

    def on_order(self, order):
        self.order_id = order.order_id
        self.datetime = order.datetime
        self.executed_volume = order.executed_volume
        self.executed_notional = order.executed_notional
        if not self.is_closed():
            self.status = order.status

    @staticmethod
    def floor(value: float, decimal_size: float):
        if pd.isna(decimal_size):
            return value
        return int(value / decimal_size) * decimal_size

    @staticmethod
    def ceil(value: float, decimal_size: float):
        if pd.isna(decimal_size):
            return value
        return int((value + decimal_size) / decimal_size) * decimal_size

    @staticmethod
    def round(value: float, decimal_size: float):
        if pd.isna(decimal_size):
            return value
        return int((value + decimal_size / 2.0) / decimal_size) * decimal_size

    def contract_check(self):
        contract = self.contract

        volume = self.volume = self.floor(self.volume, contract.lot_size)
        price = self.price = self.round(self.price, contract.tick_size)

        if contract.contract_type == EnumContractType.SPOT:
            notional = abs(volume) * price
        else:
            notional = abs(volume)

        if abs(volume) < contract.min_quantity:
            logger.debug(f'Order volume {volume} not reach the min requirement {contract.min_quantity}')
            return False
        if notional < contract.min_notional:
            logger.debug(f'Order notional {notional} not reach the min requirement {contract.min_notional}')
            return False
        if abs(volume) > contract.max_quantity:
            logger.debug(f'Order volume {volume} break the max requirement {contract.max_quantity}')
            return False
        if notional > contract.max_notional:
            logger.debug(f'Order notional {notional} break the max requirement {contract.max_notional}')
            return False
        if price < contract.min_price:
            logger.debug(f'Order price {price} not reach the min requirement {contract.min_price}')
            return False

        return True


@dataclass()
class TradeData(TradingBaseData):
    EVENT_TYPE = EnumEventType.TRADE
    COLUMN_ENUM = ['direction']

    direction: EnumOrderDirection = EnumOrderDirection.BUY
    price: float = EMPTY_FLOAT
    volume: float = EMPTY_FLOAT

    commission: float = EMPTY_FLOAT
    commission_asset: str = EMPTY_STRING

    trade_id: str = EMPTY_STRING
    order_id: str = EMPTY_STRING
    client_order_id: str = EMPTY_STRING

    @classmethod
    def from_order(cls, order: OrderData):
        trade = cls()
        trade.datetime = order.datetime
        trade.strategy_id = order.strategy_id
        trade.symbol = order.symbol

        trade.client_order_id = order.client_order_id
        trade.order_id = order.order_id

        trade.direction = order.direction
        trade.price = order.price
        trade.volume = order.volume

        return trade


@dataclass()
class FundingData(TradingBaseData):
    EVENT_TYPE = EnumEventType.FUNDING

    funding_id: str = field(default_factory=generate_id)
    volume: float = EMPTY_FLOAT
