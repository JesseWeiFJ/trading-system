#!/usr/bin/env python
# -*- coding: utf-8 -*-
from jtrader.broker.oms.order_check.check import OrderCheck
from jtrader.datatype import *
from jtrader.core.common.log import logger


class MaxPositionCheck(OrderCheck):

    TAG = 'MaxPositionCheck'

    def __init__(self, max_notional):
        super(MaxPositionCheck, self).__init__()
        self.max_notional = max_notional

    def check_order(self, order: OrderData):
        symbol = order.symbol
        present_asset_value = self.portfolio[symbol].asset_value
        if order.direction == EnumOrderDirection.BUY:
            volume = order.volume
        else:
            volume = -order.volume
        new_value = volume * order.price
        if abs(present_asset_value + new_value) > self.max_notional:
            logger.info("Present notional is %f and new notional is %f while the maximum limit is %f\n"
                        "%s", present_asset_value, new_value, self.max_notional, order)
            return False
        return True
