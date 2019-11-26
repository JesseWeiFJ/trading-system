#!/usr/bin/env python
# -*- coding: utf-8 -*-


from jtrader.datatype.positions.position import *
from jtrader.datatype.positions.swap_position import SwapPositionData
from jtrader.datatype.constants import ContractTypeAbbr


@dataclass()
class FuturesPositionData(SwapPositionData):
    # code are removed
    TAG = ContractTypeAbbr.FUTURES
