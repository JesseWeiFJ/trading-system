#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from mongoengine import DateTimeField, Document, FloatField, StringField, DictField, connect
from jtrader.datatype import *
from jtrader.core.common import Singleton, logger
from jtrader.server.database.base import DatabaseServer


class DBBalanceData(Document):
    strategy_id: str = StringField()
    datetime: datetime = DateTimeField()
    asset: str = StringField()

    price: float = FloatField()
    total_amount: float = FloatField()
    frozen_amount: float = FloatField()

    meta = {
        "indexes": [
            {
                "fields": ("strategy_id", "asset"),
                "unique": True,
            }
        ]
    }


class DBPnLData(Document):
    strategy_id: str = StringField()
    datetime: datetime = DateTimeField()

    unrealized_pnl: float = FloatField()
    realized_pnl: float = FloatField()
    total_pnl: float = FloatField()

    asset_value: float = FloatField()

    meta = {
        "indexes": [
            {
                "fields": ("strategy_id", "datetime"),
                "unique": True,
            }
        ]
    }


class DBPositionData(Document):
    strategy_id: str = StringField()
    symbol: str = StringField()
    datetime: datetime = DateTimeField()

    amount: float = FloatField()
    asset_value: float = FloatField()
    last_price: float = FloatField()
    cost: float = FloatField()
    realized_pnl: float = FloatField()
    unrealized_pnl: float = FloatField()

    meta = {
        "indexes": [
            {
                "fields": ("strategy_id", "symbol"),
                "unique": True,
            }
        ]
    }


class DBOrderData(Document):
    strategy_id: str = StringField()
    symbol: str = StringField()
    datetime: datetime = DateTimeField()

    status: str = StringField()

    order_type: str = StringField()
    direction: str = StringField()

    price: float = FloatField()
    volume: float = FloatField()
    executed_volume: float = FloatField()
    executed_notional: float = FloatField()

    order_id: str = StringField()
    client_order_id: str = StringField()

    parameter: dict = DictField()

    meta = {
        "indexes": [
            {
                "fields": ("symbol", "client_order_id"),
                "unique": True,
            }
        ]
    }


class DBTradeData(Document):
    strategy_id: str = StringField()
    symbol: str = StringField()
    datetime: datetime = DateTimeField()

    direction: str = StringField()
    volume: float = FloatField()
    price: float = FloatField()

    commission: float = FloatField()
    commission_asset: str = StringField()

    trade_id: str = StringField()
    order_id: str = StringField()
    client_order_id: str = StringField()

    meta = {
        "indexes": [
            {
                "fields": ("symbol", "order_id", "trade_id"),
                "unique": True,
            }
        ]
    }


class MongoSerevr(DatabaseServer, metaclass=Singleton):
    TAG = 'mongo'

    def configure(self, config):
        database = config["database"]
        host = config["host"]
        port = config["port"]
        username = config["username"]
        password = config["password"]
        # authentication_source = settings["authentication_source"]

        if not username:  # if username == '' or None, skip username
            username = None
            password = None
            # authentication_source = None

        connect(
            db=database,
            host=host,
            port=port,
            username=username,
            password=password,
            # authentication_source=authentication_source,
        )

    def save_order(self, order: OrderData):
        data_dict = self.update_param(order)
        DBOrderData.objects(client_order_id=order.client_order_id, symbol=order.symbol). \
            update_one(upsert=True, **data_dict)

    def save_trade(self, trade: TradeData):
        data_dict = self.update_param(trade)
        DBTradeData.objects(client_order_id=trade.trade_id, symbol=trade.symbol). \
            update_one(upsert=True, **data_dict)

    def save_position(self, position: PositionData):
        data_dict = self.update_param(position)
        DBPositionData.objects(strategy_id=position.strategy_id, symbol=position.symbol). \
            update_one(upsert=True, **data_dict)

    def save_balance(self, balance: BalanceData):
        data_dict = self.update_param(balance)
        DBBalanceData.objects(strategy_id=balance.strategy_id, asset=balance.asset). \
            update_one(upsert=True, **data_dict)

    def save_pnl(self, pnl: PnLData):
        data_dict = self.update_param(pnl)
        DBPnLData.objects(strategy_id=pnl.strategy_id, datetime=pnl.datetime). \
            update_one(upsert=True, **data_dict)

    def save(self, base_data: BaseData):
        try:
            self._save(base_data)
        except Exception as e:
            logger.exception(e)

    def _save(self, base_data: BaseData):
        if isinstance(base_data, OrderData):
            self.save_order(base_data)
        elif isinstance(base_data, TradeData):
            self.save_trade(base_data)
        elif isinstance(base_data, PositionData):
            self.save_position(base_data)
        elif isinstance(base_data, BalanceData):
            self.save_balance(base_data)
        elif isinstance(base_data, PnLData):
            self.save_pnl(base_data)
        else:
            raise TypeError('Not an expect data to store, got {}'.format(base_data))
        logger.debug('save {} to database'.format(base_data))

    @staticmethod
    def update_param(base_data: BaseData):
        data_dict = base_data.to_dict()
        update_dict = {
            'set__' + k: v for k, v in data_dict.items()
        }
        return update_dict

    @staticmethod
    def from_base_data(cls, data: BaseData):
        db_data = cls()
        data_dict = data.to_dict()
        for field_ in getattr(cls, '_fields'):
            if field_ in data_dict:
                setattr(db_data, field_, data_dict[field_])
        return db_data

    def clear(self):
        DBOrderData.drop_collection()
        DBTradeData.drop_collection()
        DBPnLData.drop_collection()
        DBPositionData.drop_collection()
        DBBalanceData.drop_collection()


if __name__ == '__main__':
    manager = MongoSerevr()
    manager.configure(dict(username='', password='', host='localhost', database='trading', port=27017))

    import uuid

    order = OrderData()

    order.order_id = str(uuid.uuid4())
    order.client_order_id = str(uuid.uuid1())
    order.strategy_id = 'test'
    manager.save(order)
