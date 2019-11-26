from jtrader.broker.gateway.websocket_api import AggregateWebsocketApi
import copy
import datetime
import hashlib
import hmac
import time
import pandas as pd
import typing

from jtrader.core.common.log import logger
from jtrader.datatype import *

statusMapReverse = dict()
statusMapReverse['New'] = EnumOrderStatus.PENDING
statusMapReverse['Partially filled'] = EnumOrderStatus.PARTIAL_FILLED
statusMapReverse['Filled'] = EnumOrderStatus.FILLED
statusMapReverse['Canceled'] = EnumOrderStatus.CANCELLED
statusMapReverse['Rejected'] = EnumOrderStatus.ERROR


class BitmexStream(AggregateWebsocketApi):
    HOST = 'wss://www.bitmex.com/realtime'

    def __init__(self, api):
        super(BitmexStream, self).__init__(api)
        self._order_dict: typing.Dict[str, OrderData] = {}
        self._callback_dict = {
            'orderBook10': self._on_depth,
            'funding': self._on_funding_rate,

            'execution': self._on_trade,
            'order': self._on_order,
        }

    def subscribe_bar(self, symbol, frequency):

        bar = BarData()
        bar.symbol = symbol
        bar.frequency = frequency
        self._bar_dict[(symbol, frequency)] = bar

        symbol_exchange = self.api.contracts[symbol].symbol_exchange
        topic = "tradeBin%s" % frequency
        if topic not in self._callback_dict:
            self._callback_dict[topic] = self._on_bar_impl2(frequency)
        req = {"op": "subscribe", "args": ["tradeBin%s:%s" % (frequency, symbol_exchange)]}
        self.send_packet(req)

    def subscribe_depth(self, symbol):
        depth = DepthData()
        depth.symbol = symbol
        self._depth_dict[symbol] = depth

        symbol_exchange = self.api.contracts[symbol].symbol_exchange
        req = {"op": "subscribe", "args": ["orderBook10:%s" % symbol_exchange]}

        self.send_packet(req)

    def subscribe_user_stream(self):
        expires = int(time.time() + 5) * 1000
        method = 'GET'
        path = '/realtime'
        msg = method + path + str(expires)
        signature = hmac.new(self.api.api_secret.encode('utf-8'), msg.encode('utf-8'),
                             digestmod=hashlib.sha256).hexdigest()

        req = {
            'op': 'authKey',
            'args': [self.api.api_key, expires, signature]
        }
        self.send_packet(req)

        req = {
            'op': 'subscribe',
            'args': ['execution', 'order']
        }
        self.send_packet(req)

    def _parse_depth(self, packet, depth: DepthData):
        depth.datetime = datetime.datetime.utcnow()
        bids = packet['bids']
        for index, (price, volume) in enumerate(bids[:DepthData.N_DEPTH]):
            depth.bid_prices[index] = price
            depth.bid_volumes[index] = volume
        asks = packet['asks']
        for index, (price, volume) in enumerate(asks[:DepthData.N_DEPTH]):
            depth.ask_prices[index] = price
            depth.ask_volumes[index] = volume

    def _on_depth(self, data):
        symbol_exchange = data['symbol']
        symbol = self.api.exchange_symbol_dict[symbol_exchange]
        depth = self._depth_dict[symbol]
        self._parse_depth(data, depth)
        self.api.on_depth(copy.copy(depth))

    def _on_funding_rate(self, data):
        symbol_exchange = data['symbol']
        symbol = self.api.exchange_symbol_dict[symbol_exchange]
        funding_rate = FundingRateData()
        funding_rate.symbol = symbol
        funding_rate.datetime = pd.to_datetime(data['timestamp'])
        funding_rate.rate = data['fundingRate']
        self.api._callback(funding_rate)

    def _parse_bar(self, packet, bar: BarData):
        bar.open = packet['open']
        bar.high = packet['high']
        bar.low = packet['low']
        bar.close = packet['close']
        bar.volume = packet['volume']
        bar.datetime = pd.to_datetime(packet['timestamp']).replace(tzinfo=None) - TIME_INTERVAL_MAP[bar.frequency]

    def _on_bar_impl2(self, frequency):
        def callback(data):
            symbol = self.api.exchange_symbol_dict[data['symbol']]
            bar = self._bar_dict[(symbol, frequency)]
            self._parse_bar(data, bar)
            self.api.on_bar(copy.copy(bar))

        return callback

    def _on_trade(self, data):
        # print('Original trade: %s' % data)
        logger.debug('raw trade data: %s', data)
        if not data['lastQty']:
            return

        trade_id = data['execID']

        symbol_exchange = data['symbol']
        symbol = self.api.exchange_symbol_dict[symbol_exchange]

        if not data['side']:
            # funding = FundingData()
            # funding.symbol = 'USD.BTX'
            # funding.volume = data['commission'] * data['lastQty']
            # funding.funding_id = trade_id
            # self.callback(funding)
            trade = TradeData()
            trade.trade_id = trade_id
            trade.symbol = symbol
            trade.volume = 0.0
            trade.price = 0.0
            trade.commission = data['commission'] * data['lastQty']
            trade.commission_asset = 'USD.BTX'
            self.api.on_trade(trade)
            return

        cli_id = data['clOrdID']
        order = self.api.oms[cli_id]
        trade = TradeData.from_order(order)

        trade.order_id = data['orderID']
        trade.trade_id = trade_id
        trade.price = data['lastPx']
        trade.volume = data['lastQty']
        trade.datetime = pd.to_datetime(data['timestamp'])
        trade.commission = data['commission'] * trade.volume
        trade.commission_asset = self.api.contracts[trade.symbol].asset_quote
        logger.debug('%s receive: %s', self, trade)
        self.api.on_trade(trade)

    def _on_order(self, data):
        logger.debug('raw order data: %s', data)
        if 'ordStatus' not in data:
            return

        cli_id = data['clOrdID']

        order = self.api.oms.clone(cli_id)
        if order:
            order.order_id = data['orderID']
            order.datetime = pd.to_datetime(data['timestamp'])

            order.executed_volume = data.get('cumQty', order.executed_volume)
            order.status = statusMapReverse.get(data['ordStatus'], EnumOrderType.NONE)
            logger.debug('%s receive: %s', self, order)

            self.api.on_order(copy.copy(order))

    def on_packet(self, data: dict):
        if 'table' in data:
            name = data['table']
            if name in self._callback_dict:
                callback = self._callback_dict[name]
                if isinstance(data['data'], list):
                    for data in data['data']:
                        callback(data)
                else:
                    callback(data['data'])
            else:
                logger.debug("BitMex received other data: %s", data)

        elif 'request' in data:
            req = data['request']
            if 'success' in data:
                success = data['success']
                flag = 'succeeded' if success else 'failed'
                logger.debug("request for operation %s %s", req, flag)
            else:
                logger.info("request failed %s with error %s", req, data['error'])
        else:
            logger.debug("BitMex received other data: %s", data)

    # def _ping(self):
    #     pass
