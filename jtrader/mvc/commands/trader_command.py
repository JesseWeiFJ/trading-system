#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from jtrader.trader import StrategyTemplate, Trader as _Actor
from jtrader.core.common.utils import parse_file
from jtrader.datatype import *
from jtrader.mvc.commands.command import CommandBaseData
from jtrader.core.common.log import logger

ALL_STRATEGY = 'ALL'


@dataclass
class TraderCommand(CommandBaseData):
    ACTOR = _Actor.__name__

    def execute(self, actor: _Actor):
        pass


@dataclass
class ShowAlgorithmCommand(TraderCommand):
    def execute(self, actor: _Actor):
        self.render(actor.query_algorithms())


@dataclass
class AddStrategyCommand(TraderCommand):
    config_file: str = EMPTY_STRING

    def parse(self, cmd_str: str):
        command_args = self.split(cmd_str)
        self.config_file = command_args[0]

    def execute(self, actor: _Actor):
        strategy_config = parse_file(self.config_file)
        strategy = actor.create_strategy(strategy_config)
        actor.add_strategy(strategy)
        logger.info('Add %s with %s', strategy, strategy_config)


@dataclass
class ModifyStrategyCommand(TraderCommand):
    config_file: str = EMPTY_STRING
    strategy_id: str = EMPTY_STRING

    def parse(self, cmd_str: str):
        command_args = self.split(cmd_str)
        self.strategy_id = command_args[0]
        if len(command_args) > 1:
            self.config_file = command_args[1]

    def execute(self, actor: _Actor):
        strategy = actor.strategy_dict[self.strategy_id]
        if not self.config_file:
            strategy.reconfigure()
        else:
            strategy_config = parse_file(self.config_file)
            actor.modify_strategy(strategy_config)
            logger.info('Modify with %s', strategy_config)
        strategy.on_init()


@dataclass
class RemoveStrategyCommand(TraderCommand):
    strategy_id: str = EMPTY_STRING

    def parse(self, cmd_str: str):
        command_args = self.split(cmd_str)
        self.strategy_id = command_args[0]

    def execute(self, actor: _Actor):
        actor.remove_strategy(self.strategy_id)


@dataclass
class StrategyCommand(TraderCommand):
    ACTOR = _Actor.__name__

    strategy_id: str = EMPTY_STRING

    def split(self, cmd_str: str):
        command_args = super(StrategyCommand, self).split(cmd_str)
        if len(command_args) == 0:
            self.strategy_id = ALL_STRATEGY
        else:
            self.strategy_id = command_args[0]
        return command_args

    def execute(self, actor: _Actor):
        if self.strategy_id.upper() == ALL_STRATEGY:
            strategy_list = actor.strategy_dict.values()
        elif self.strategy_id in self.strategy_id:
            strategy_list = [actor.strategy_dict[self.strategy_id], ]
        else:
            logger.info('strategy_id %s does not exist', self.strategy_id)
            return
        for strategy in strategy_list:
            try:
                self.single_command_impl(strategy)
            except Exception as e:
                logger.exception(e)
                logger.info("Failing to execute commands %s for %s", self, strategy)

    def single_command_impl(self, strategy: StrategyTemplate):
        pass


@dataclass
class SetModeCommand(StrategyCommand):
    mode: EnumTradingMode = EnumTradingMode.OFF

    def parse(self, cmd_str: str):
        command_args = self.split(cmd_str)
        self.mode = EnumTradingMode.get_enum(command_args[1])

    def single_command_impl(self, strategy: StrategyTemplate):
        strategy.set_mode(self.mode)


@dataclass
class ShowStatusCommand(StrategyCommand):
    verbose: bool = False

    def parse(self, cmd_str: str):
        command_args = self.split(cmd_str)
        if len(command_args) >= 2:
            content = command_args[1].upper()
            self.verbose = content == 'ALL'

    def single_command_impl(self, strategy: StrategyTemplate):
        status = strategy.get_running_status()
        self.render(status)


@dataclass
class ShowMarketCommand(StrategyCommand):
    def parse(self, cmd_str: str):
        self.split(cmd_str)

    def single_command_impl(self, strategy: StrategyTemplate):
        self.render(strategy.get_market_signal())


@dataclass
class FundingCommand(StrategyCommand):
    asset: str = EMPTY_STRING
    volume: float = EMPTY_FLOAT

    def parse(self, cmd_str: str):
        command_args = self.split(cmd_str)
        self.asset = command_args[1]
        self.volume = float(command_args[2])

    def execute(self, actor: _Actor):
        funding = FundingData()
        funding.strategy_id = self.strategy_id
        funding.volume = self.volume
        funding.symbol = self.asset
        actor.strategy_dict[self.strategy_id].on_funding(funding)


@dataclass
class ClosePositionCommand(StrategyCommand):
    symbol: str = EMPTY_STRING

    def parse(self, cmd_str: str):
        command_args = self.split(cmd_str)
        self.symbol = command_args[1]

    def single_command_impl(self, strategy: StrategyTemplate):
        if self.symbol.upper() == 'ALL':
            strategy.close_all()
        else:
            strategy.close_position(self.symbol)


@dataclass
class SavePortfolioCommand(StrategyCommand):
    file_name: str = EMPTY_STRING

    def parse(self, cmd_str: str):
        command_args = self.split(cmd_str)
        if len(command_args) > 1:
            self.file_name = command_args[1]

    def single_command_impl(self, strategy: StrategyTemplate):
        strategy.save_portfolio(self.file_name)
        logger.info('Save portfolio\n' + strategy.portfolio.describe())


@dataclass
class LoadPortfolioCommand(StrategyCommand):
    file_name: str = EMPTY_STRING

    def parse(self, cmd_str: str):
        command_args = self.split(cmd_str)
        if len(command_args) > 1:
            self.file_name = command_args[1]

    def single_command_impl(self, strategy: StrategyTemplate):
        strategy.load_portfolio(self.file_name)
        logger.info('Load portfolio\n' + strategy.portfolio.describe())


@dataclass
class CreateOrderCommand(TraderCommand):
    ACTOR = _Actor.__name__
    order: OrderData = OrderData()

    def execute(self, actor: _Actor):
        logger.info("Execute algorithm for: \n%s", self.order.pretty_string())
        actor.send_order(self.order)

    def parse(self, cmd_str: str):
        command_args = self.split(cmd_str)
        self.order = OrderData()
        self.order.order_type = EnumOrderType.get_enum(command_args[0])
        self.order.direction = EnumOrderDirection.get_enum(command_args[1])
        self.order.volume = float(command_args[2])
        self.order.symbol = command_args[3].upper()

        if len(command_args) > 4:
            self.order.price = float(command_args[4])
        if len(command_args) > 5:
            self.order.strategy_id = command_args[5]
        else:
            self.order.strategy_id = 'manual'
        if len(command_args) > 6:
            self.order.parameter = json.loads(command_args[6])

        self.order.client_order_id = generate_id()
        self.order.status = EnumOrderStatus.NEW


@dataclass
class CancelOrderCommand(TraderCommand):
    order: OrderData = OrderData()

    def parse(self, cmd_str: str):
        command_args = self.split(cmd_str)
        self.order = OrderData()
        self.order.status = EnumOrderStatus.CANCELLING
        self.order.client_order_id = command_args[0]
        self.order.strategy_id = command_args[1]

    def execute(self, actor: _Actor):
        if self.order.strategy_id == 'algo':
            self.order.order_type = EnumOrderType.BLP
            actor.send_order(self.order)
        else:
            actor.strategy_dict[self.order.strategy_id].cancel_order(self.order.client_order_id)
