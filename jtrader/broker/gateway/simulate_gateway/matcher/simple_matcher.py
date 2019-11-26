#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jtrader.broker.gateway.simulate_gateway.matcher.matcher import Matcher
from jtrader.datatype import *
from jtrader.core.common import logger
from jtrader.datatype.markets import ContractData


class SimpleMatcher(Matcher):
    TAG = 'simple'

    def match_order(self, order: OrderData):
        logger.debug(f'{self} got order {order}')

        if EnumOrderStatus.NEW == order.status:
            order.status = EnumOrderStatus.FILLED
            order.executed_volume = order.volume
            order.order_id = generate_id()

            trade = TradeData.from_order(order)
            trade.trade_id = generate_id()

            if trade.direction == EnumOrderDirection.BUY:
                trade.price = trade.price * (1 + self.slippage)
            else:
                trade.price = trade.price * (1 - self.slippage)

            trade.commission_asset = order.contract.asset_quote
            trade.commission = trade.price * trade.volume * self.fee_rate

            self.callback(trade)
            self.callback(order)

        elif EnumOrderStatus.CANCELLING == order.status:
            order.status = EnumOrderStatus.CANCELLED
            self.callback(order)
