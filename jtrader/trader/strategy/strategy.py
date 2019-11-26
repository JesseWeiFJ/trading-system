import os
import typing
import pickle
import pandas as pd
from collections import OrderedDict

from jtrader.core.common import logger, Configurable, import_class
from jtrader.datatype import *
from jtrader.datatype.portfolio import Portfolio
from jtrader.datatype.base import BaseData, dataclass, field
from jtrader.trader.interface import TradingTemplate
from jtrader.trader.algo import AlgorithmEngine
from jtrader.trader.strategy.risk import RiskControl, RiskControlFactory


@dataclass
class StrategyConfigInfo(BaseData):
    strategy_id: str = ''
    strategy_type: str = ''
    universe: typing.List[str] = field(default_factory=list)
    positions: typing.Dict[str, float] = field(default_factory=dict)
    arguments: typing.Dict = field(default_factory=dict)
    accounting_unit: str = 'USDT'
    risks: typing.Dict = field(default_factory=dict)


class StrategyTemplate(Configurable, TradingTemplate):
    subclass_dict = {}

    def __init_subclass__(cls, **kwargs):
        super(StrategyTemplate, cls).__init_subclass__(**kwargs)
        cls.subclass_dict[cls.__name__] = cls

    @property
    def portfolio(self):
        return self._portfolio

    @property
    def id_(self):
        return self._strategy_id

    @property
    def broker(self):
        return self.algorithm_engine

    @property
    def universe(self):
        return self._universe

    def __init__(self):
        super(StrategyTemplate, self).__init__()
        self._strategy_id = ""
        self._universe = []
        self._portfolio: Portfolio = None
        self._risk_list: typing.List[RiskControl] = []

        self.algorithm_engine: AlgorithmEngine = None

    def configure(self, strategy_config: StrategyConfigInfo):
        self._strategy_id = strategy_config.strategy_id
        self._universe = strategy_config.universe
        self._portfolio = Portfolio(self._strategy_id, strategy_config.accounting_unit)

        for key, value in strategy_config.positions.items():
            self._portfolio.adjust_asset(key, value)

        for key, value in strategy_config.arguments.items():
            setattr(self, key, value)

        self._risk_list.clear()
        for key, value in strategy_config.risks.items():
            risk = RiskControlFactory(key, **value)
            self._risk_list.append(risk)
            logger.info('Risk Control %s is added to %s', risk, self)

        logger.info("Configure %s with %s", self, strategy_config.pretty_string())
        self.on_init()

    def save_portfolio(self, file_name=''):
        if not file_name:
            file_name = '.'.join([self._strategy_id, 'portfolio'])
        with open(file_name, 'wb') as f:
            pickle.dump(self._portfolio, f)

    def load_portfolio(self, file_name=''):
        if not file_name:
            file_name = '.'.join([self._strategy_id, 'portfolio'])
        if os.path.exists(file_name):
            with open(file_name, 'rb') as f:
                self._portfolio = pickle.load(f)

    def update_portfolio(self):
        for symbol, bar in self._bar_dict.items():
            self.portfolio.on_bar(bar)
        for symbol, depth in self._depth_dict.items():
            self.portfolio.on_depth(depth)

    def order_target(self, symbol, volume, price_level=-2):
        # todo: change price level to slippage object or order handler object
        present_holding = self.portfolio.available_base_amount(symbol)
        to_place_volume = volume - present_holding
        self.order(symbol, to_place_volume, price_level)

    def order_value(self, symbol, value, price_level=-2):
        if value > 0:
            direction = EnumOrderDirection.BUY
        else:
            direction = EnumOrderDirection.SELL
        price = self.choose_price(symbol, direction, price_level)
        volume = value / price
        self.order(symbol, volume, price_level)

    def order_target_value(self, symbol, value, price_level=-2):
        to_place_value = value - self.portfolio[symbol].asset_value
        self.order_value(symbol, to_place_value, price_level)

    def on_subscribe(self):
        super(StrategyTemplate, self).on_subscribe()
        self.subscribe(EnumEventType.HEARTBEAT, self.on_heartbeat)
        self.subscribe(EnumEventType.ORDER + self.id_, self.on_order_status)
        self.subscribe(EnumEventType.TRADE + self.id_, self.on_trade)
        self.subscribe(EnumEventType.FUNDING + self.id_, self.on_funding)
        for symbol in self._universe:
            self.subscribe(EnumEventType.BAR + symbol, self.on_bar)
            self.subscribe(EnumEventType.DEPTH + symbol, self.on_depth)

    def on_order_status(self, order: OrderData):
        super(StrategyTemplate, self).on_order_status(order)
        self.portfolio.on_order_status(order)

    def on_trade(self, trade: TradeData):
        super(StrategyTemplate, self).on_trade(trade)
        self.portfolio.on_trade(trade)

    def on_funding(self, funding: FundingData):
        super(StrategyTemplate, self).on_funding(funding)
        self.portfolio.on_funding(funding)

    def on_heartbeat(self, heartbeat: HeartBeatData):
        super(StrategyTemplate, self).on_heartbeat(heartbeat)
        if heartbeat.frequency != '1s':
            for risk in self._risk_list:
                risk.check_risk(self)

    def close_position(self, symbol: str, multiple: float = 1.0):
        volume = self.portfolio.available_base_amount(symbol) * multiple
        if abs(volume) > ContractData.get_contract(symbol).min_quantity:
            self.order(symbol, -volume)

    def close_all(self):
        self.cancel_all()
        for position in self.portfolio:
            self.close_position(position.symbol)

    def get_market_signal(self):
        depth_str_list = [depth.pretty_string() for depth in self.depth_dict.values()]
        depth_str = '\n'.join(depth_str_list)
        market_string = "------------------------------\n" \
                        "Strategy: %s\n" \
                        "Market data:\n" \
                        "Depth:\n%s\n" \
                        % \
                        (
                            self,
                            depth_str,
                        )
        return market_string

    def get_running_status(self):
        self.update_portfolio()
        order_df = pd.DataFrame([x.to_dict(OrderedDict) for x in self.working_order_dict.values()])
        order_str = order_df.to_string() if len(order_df) else "[]"

        portfolio_str = self.portfolio.describe()

        status_string = "------------------------------\n" \
                        "Strategy: %s\n" \
                        "ID: %s\n" \
                        "Status: %s\n" \
                        "Datetime: %s\n" \
                        "Working orders: \n%s\n" \
                        "------------------------------\n" \
                        "%s\n" \
                        % \
                        (
                            self,
                            self.id_,
                            self.trading_mode,
                            self.datetime,
                            order_str,
                            portfolio_str,
                        )

        return status_string


class StrategyFactory(object):
    def __new__(cls, name: str) -> StrategyTemplate:
        if name in StrategyTemplate.subclass_dict:
            strategy_class = StrategyTemplate.subclass_dict[name]
        else:
            strategy_class = import_class(name)
        strategy_instance = strategy_class()
        return strategy_instance
