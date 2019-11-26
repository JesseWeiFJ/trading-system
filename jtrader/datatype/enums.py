#!/usr/bin/env python
# -*- coding: utf-8 -*-
from enum import auto, unique, IntEnum as _IntEnum


class IntEnum(_IntEnum):
    def __add__(self, other):
        return self, other

    @classmethod
    def int_enum_map(cls, reverse=False):
        enum_map = {}
        for enum in cls:
            if not reverse:
                enum_map[enum.value] = enum
            else:
                enum_map[enum] = enum.value
        return enum_map

    @classmethod
    def get_enum(cls, name: str):
        return getattr(cls, name.upper())


class EnumTradingMode(IntEnum):
    OFF = auto()
    MANUAL = auto()
    AUTO = auto()


class EnumOrderDirection(IntEnum):
    BUY = auto()
    SELL = auto()

    def __neg__(self):
        if self == self.BUY:
            return self.SELL
        elif self == self.SELL:
            return self.BUY
        else:
            return self


class EnumOffSet(IntEnum):
    OPEN = auto()
    CLOSE = auto()


class EnumFundingDirection(IntEnum):
    DEPOSIT = auto()
    WITHDRAW = auto()


class EnumOrderStatus(IntEnum):
    NEW = auto()
    PENDING = auto()
    PARTIAL_FILLED = auto()
    FILLED = auto()
    CANCELLING = auto()
    CANCELLED = auto()
    CANCEL_ERROR = auto()
    ERROR = auto()  # recoverable
    REJECTED = auto()  # unrecoverable

    @classmethod
    def open_status(cls):
        return [cls.PARTIAL_FILLED, cls.PENDING, cls.NEW, cls.CANCEL_ERROR, cls.CANCELLING]

    @classmethod
    def closed_status(cls):
        return [cls.FILLED, cls.CANCELLED, cls.ERROR, cls.REJECTED]


class EnumOrderType(IntEnum):
    NONE = auto()
    LIMIT = auto()
    MARKET = auto()
    BLP = auto()
    VWAP = auto()
    TWAP = auto()
    BUY_BACK = auto()
    STOP = auto()
    SOR = auto()

    @classmethod
    def origin_types(cls):
        return [cls.LIMIT, cls.MARKET]

    @classmethod
    def derivative_types(cls):
        return [cls.BLP, cls.VWAP, cls.TWAP, cls.BUY_BACK, cls.STOP, cls.SOR]


class EnumEventType(IntEnum):
    DEPTH = auto()
    BAR = auto()
    CONTRACT = auto()
    HEARTBEAT = auto()
    FUNDING_RATE = auto()

    TRADE = auto()
    ORDER = auto()
    FUNDING = auto()
    POSITION = auto()

    COMMAND = auto()
    REQUEST = auto()


class EnumContractType(IntEnum):
    SPOT = auto()
    SWAP = auto()
    FUTURES = auto()
    OPTION = auto()
    FX = auto()


class EnumBookDirection(IntEnum):
    BID = auto()
    ASK = auto()


OPEN_STATUS_SET = set(EnumOrderStatus.open_status())
FINISHED_STATUS_SET = set(EnumOrderStatus.closed_status())
ORIGIN_ORDER_TYPES = set(EnumOrderType.origin_types())
DERIVATIVE_ORDER_TYPES = set(EnumOrderType.derivative_types())
