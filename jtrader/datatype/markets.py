#!/usr/bin/env python
# -*- coding: utf-8 -*-
from jtrader.datatype.base import *
from jtrader.datatype.enums import EnumEventType
from jtrader.datatype.constants import TIME_INTERVAL_MAP
import datetime as dt
import typing
import pandas as pd
import os


@dataclass
class MarketBaseData(BaseData):
    pass


@dataclass
class HeartBeatData(MarketBaseData):
    EVENT_TYPE = EnumEventType.HEARTBEAT
    frequency: str = '1s'


@dataclass
class FundingRateData(MarketBaseData):
    EVENT_TYPE = EnumEventType.FUNDING_RATE

    symbol: str = EMPTY_STRING
    rate: float = EMPTY_FLOAT


_n_depth = 5


def _depth_initialize():
    return [0.0] * _n_depth


@dataclass
class DepthData(MarketBaseData):
    EVENT_TYPE = EnumEventType.DEPTH
    N_DEPTH = _n_depth

    symbol: str = EMPTY_STRING
    ask_prices: typing.List[float] = field(default_factory=_depth_initialize)
    ask_volumes: typing.List[float] = field(default_factory=_depth_initialize)
    bid_prices: typing.List[float] = field(default_factory=_depth_initialize)
    bid_volumes: typing.List[float] = field(default_factory=_depth_initialize)

    def pretty_string(self):
        level_format = "%12.6f   %12.6f"
        bid_level_str_list = []
        ask_level_str_list = []
        for i in range(self.N_DEPTH):
            ask_level_str = level_format % (
                self.ask_prices[self.N_DEPTH - 1 - i], self.ask_volumes[self.N_DEPTH - 1 - i])
            bid_level_str = level_format % (self.bid_prices[i], self.bid_volumes[i])
            bid_level_str_list.append(bid_level_str)
            ask_level_str_list.append(ask_level_str)

        bid_str = '\n'.join(bid_level_str_list)
        ask_str = '\n'.join(ask_level_str_list)

        string_format = "symbol %s\n" \
                        "time   %s\n" \
                        "ask\n" \
                        "%s\n" \
                        "bid\n" \
                        "%s\n"
        depth_str = string_format % (self.symbol, self.datetime, ask_str, bid_str)
        return depth_str


@dataclass()
class MarketTradeData(MarketBaseData):
    EVENT_TYPE = EnumEventType.TRADE
    COLUMN_ENUM = ['direction']

    trade_id: str = EMPTY_STRING

    client_order_id: str = EMPTY_STRING
    order_id: str = EMPTY_STRING

    price: float = EMPTY_FLOAT
    volume: float = EMPTY_FLOAT


@dataclass
class BarData(MarketBaseData):
    EVENT_TYPE = EnumEventType.BAR

    symbol: str = EMPTY_STRING
    frequency: str = EMPTY_STRING
    open: float = EMPTY_FLOAT
    high: float = EMPTY_FLOAT
    low: float = EMPTY_FLOAT
    close: float = EMPTY_FLOAT
    volume: float = EMPTY_FLOAT

    def settle_time(self):
        return self.datetime + TIME_INTERVAL_MAP[self.frequency]


@dataclass
class ContractData(MarketBaseData):
    EVENT_TYPE = EnumEventType.CONTRACT

    active: bool = True
    contract_type: str = EMPTY_STRING
    symbol: str = EMPTY_STRING  # unique in whole trader system
    symbol_base: str = EMPTY_STRING
    symbol_quote: str = EMPTY_STRING
    symbol_exchange: str = EMPTY_STRING
    symbol_root: str = EMPTY_STRING
    exchange: str = EMPTY_STRING

    asset_base: str = EMPTY_STRING
    asset_quote: str = EMPTY_STRING

    multiplier: int = 1
    lot_size: float = EMPTY_FLOAT
    tick_size: float = EMPTY_FLOAT

    max_price: float = MAX_FLOAT
    min_price: float = EMPTY_FLOAT
    max_quantity: float = MAX_FLOAT
    min_quantity: float = EMPTY_FLOAT

    max_notional: float = MAX_FLOAT
    min_notional: float = EMPTY_FLOAT

    _contracts = {}

    @classmethod
    def contracts(cls) -> typing.Dict[str, "ContractData"]:
        if not cls._contracts:
            file_path = os.path.join(os.path.dirname(__file__), 'contracts.csv')
            contract_df = pd.read_csv(file_path, index_col=False)
            cls.reset_contracts(contract_df)
        return cls._contracts

    @classmethod
    def reset_contracts(cls, contract_df):
        contract_docs = contract_df.to_dict('records')
        for doc in contract_docs:
            contract = ContractData.from_dict(doc)
            cls._contracts[contract.symbol] = contract
        return cls._contracts

    @classmethod
    def get_contract(cls, symbol):
        contract: cls = cls.contracts()[symbol]
        return contract


if __name__ == '__main__':
    depth_1 = DepthData()
    depth_1.bid_volumes[0] = 10
    depth_2 = DepthData()
    print(depth_2.bid_volumes[0])
    print(depth_1.pretty_string())
    print(depth_2.pretty_string())
