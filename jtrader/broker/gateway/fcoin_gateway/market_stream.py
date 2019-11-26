from jtrader.broker.gateway.websocket_api import MarketWebsocketApi
from jtrader.datatype import *
from jtrader.core.common import logger

import datetime
import time
import websocket


class FCoinMarketStream(MarketWebsocketApi):
    HOST = 'wss://api.fcoin.com/v2/ws'
    FREQUENCY_MAP = {
        '1m': 'M1',
        '3m': 'M3',
        '5m': 'M5',
        '15m': 'M15',
        '30m': 'M30',
        '1h': 'H1',
        '4h': 'H4',
        '6h': 'H6',
        '1d': 'D1',
    }

    def on_connected(self):
        if self._depth_flag:
            self._subscribe_depth(self._symbol_list)
        for frequency in self._frequency_list:
            self._subscribe_bar(self._symbol_list, frequency)

    def subscribe_depth(self, symbol):
        self._subscribe_depth([symbol])

    def subscribe_bar(self, symbol, frequency):
        self._subscribe_bar([symbol], frequency)

    def _subscribe_depth(self, symbol_list):
        topic_list = []
        for symbol in symbol_list:
            symbol_exchange = self.api.contracts[symbol].symbol_exchange
            topic = "depth.L20.%s" % symbol_exchange
            self._callback_dict[topic] = self._on_depth_impl(symbol)
            topic_list.append(topic)
        req = {"cmd": "sub", "args": topic_list}
        self.send_packet(req)

    def _subscribe_bar(self, symbol_list, frequency):
        freq = self.FREQUENCY_MAP[frequency]
        topic_list = []
        for symbol in symbol_list:
            symbol_exchange = self.api.contracts[symbol].symbol_exchange
            topic = "candle.{freq}.{symbol}".format(freq=freq, symbol=symbol_exchange)
            if topic not in self._callback_dict:
                self._callback_dict[topic] = self._on_bar_impl(symbol, frequency)
            topic_list.append(topic)
        req = {"cmd": "sub", "args": topic_list}
        self.send_packet(req)

    def _parse_depth(self, packet, depth: DepthData):
        bids = packet['bids']
        asks = packet['asks']
        depth.datetime = datetime.datetime.utcnow()
        for index in range(DepthData.N_DEPTH):
            depth.bid_prices[index] = bids[index * 2]
            depth.bid_volumes[index] = bids[index * 2 + 1]

            depth.ask_prices[index] = asks[index * 2]
            depth.ask_volumes[index] = asks[index * 2 + 1]

    def _parse_bar(self, data, bar: BarData):
        now = datetime.datetime.utcnow()
        bar.datetime = self.round_dt(now, bar.frequency)
        bar.open = data['open']
        bar.high = data['high']
        bar.low = data['low']
        bar.close = data['close']
        bar.volume = data['base_vol']

    def _ping(self):
        request = {
            "cmd": "ping",
            "args": [int(time.time() * 1000)],
            "id": f"{time.time()}"
        }
        try:
            self.send_packet(request)
        except websocket.WebSocketConnectionClosedException as e:
            logger.exception(e)

    def on_packet(self, packet: dict):
        if 'type' in packet:
            name = packet['type']
            if name in self._callback_dict:
                callback = self._callback_dict[name]
                callback(packet)
            elif name == 'ping':
                pass
            else:
                logger.debug("%s received data without corresponding callback: %s", self, packet)
        else:
            logger.debug("%s received other data: %s", self, packet)
