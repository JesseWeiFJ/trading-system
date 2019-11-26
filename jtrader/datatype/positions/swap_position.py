#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jtrader.datatype.positions.position import *
from jtrader.datatype.constants import ContractTypeAbbr
from jtrader.datatype.enums import EnumOrderDirection
from jtrader.datatype.markets import ContractData


@dataclass()
class SwapPositionData(PositionData):
    # codes are removed
    TAG = ContractTypeAbbr.SWAP
