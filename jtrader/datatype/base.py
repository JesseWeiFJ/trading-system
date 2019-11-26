#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dataclasses import dataclass, asdict, astuple, fields, field
import datetime as dt
import pandas as pd
import typing
import copy
from collections import OrderedDict
from jtrader.datatype.enums import EnumEventType

EMPTY_FLOAT = 0.0
EMPTY_INT = 0
MAX_FLOAT = float('inf')
EMPTY_STRING = ''

__all__ = [
    'BaseData',
    'field',
    'dataclass',
    'EMPTY_FLOAT',
    'MAX_FLOAT',
    'EMPTY_STRING',
    'EMPTY_INT',
]


@dataclass
class BaseData(object):
    EVENT_TYPE = EnumEventType

    datetime: dt.datetime = field(default_factory=dt.datetime.utcnow)

    def to_dict(self, dict_factory: typing.Type[dict] = dict) -> dict:
        return asdict(self, dict_factory=dict_factory)

    def to_tuple(self, tuple_factory: typing.Type[tuple] = tuple) -> tuple:
        return astuple(self, tuple_factory=tuple_factory)

    @classmethod
    def to_df(cls, data_list):
        record_list = []
        for data in data_list:
            record_list.append(data.to_dict(OrderedDict))
        data_df = pd.DataFrame(record_list)
        return data_df

    @classmethod
    def from_dict(cls, data_dict: dict):
        data = cls()
        field_dict = cls.__dict__['__dataclass_fields__']
        for key, value in data_dict.items():
            if key in field_dict:
                setattr(data, key, value)
        return data

    @classmethod
    def from_df(cls, df: pd.DataFrame):
        data_list = [None] * len(df)
        records = df.to_dict('records')
        for index, record in enumerate(records):
            data = cls.from_dict(record)
            data_list[index] = data
        return data_list

    @classmethod
    def fields(cls):
        return [f.name for f in fields(cls)]

    def pretty_string(self):
        field_dict = self.to_dict(OrderedDict)
        head = self.__class__.__name__
        field_str_list = ['\t%s: %s' % (k, v) for k, v in field_dict.items()]
        data_str = '\n'.join(field_str_list)
        return '\n'.join([head, data_str])

    def copy(self):
        return copy.copy(self)
