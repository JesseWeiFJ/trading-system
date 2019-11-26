#!/usr/bin/env python
# -*- coding: utf-8 -*-
from jtrader.broker.oms.order_check.check import OrderCheck
from jtrader.datatype import *
from jtrader.core.common import logger


class MaxNotionalCheck(OrderCheck):
    TAG = 'MaxNotionalCheck'

    def __init__(self, max_notional=None):
        super(MaxNotionalCheck, self).__init__()
        self.max_notional = max_notional

    def check_order(self, order: OrderData):
        notional = abs(order.price * order.volume)
        if notional > self.max_notional:
            logger.info("Order notional %f excess the maximum value %f\n%s", order.volume, self.max_notional, order)
            return False
        return True
