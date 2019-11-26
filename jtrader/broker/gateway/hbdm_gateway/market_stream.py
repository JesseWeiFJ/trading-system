from jtrader.broker.gateway.websocket_api import MarketWebsocketApi
from jtrader.broker.gateway.hbdm_gateway.base_stream import HBDMStreamMixin
from jtrader.datatype import *
from jtrader.core.common import logger

import datetime
import time

CONTRACT_TYPE_MAP = {
    "this_week": "CW",
    "next_week": "NW",
    "quarter": "CQ"
}


class HBDMMarketStream(HBDMStreamMixin, MarketWebsocketApi):
    HOST = "wss://www.hbdm.com/ws"

    FREQUENCY_MAP = {
        '1m': "1min",
        '5m': "5min",
        '15m': "15min",
        '30m': "30min",
        '1h': "60min",
        '4h': "4hour",
        '1d': "1day"
    }

    def subscribe_depth(self, symbol):
        ws_symbol = self._get_exchange_symbol(symbol)
        topic = f"market.{ws_symbol}.depth.step0"
        callback = self._on_depth_impl(symbol)
        self._callback_dict[topic] = callback

        req = {
            "sub": topic,
            "id": f'{time.time()}'
        }
        self.send_packet(req)

    def subscribe_bar(self, symbol, frequency):
        ws_symbol = self._get_exchange_symbol(symbol)
        freq = self.FREQUENCY_MAP[frequency]
        topic = f"market.{ws_symbol}.kline.{freq}"
        callback = self._on_bar_impl(symbol, frequency)
        self._callback_dict[topic] = callback
        req = {
            "sub": topic,
            "id": f'{time.time()}'
        }
        self.send_packet(req)

    def _get_exchange_symbol(self, symbol):
        contract_type = self.api.symbol_type_map.get(symbol, "")
        if not contract_type:
            return

        asset = self.api.contracts[symbol].symbol_base

        ws_contract_type = CONTRACT_TYPE_MAP[contract_type]
        ws_symbol = f"{asset}_{ws_contract_type}"
        return ws_symbol

    def _parse_depth(self, packet, depth: DepthData):
        dt = datetime.datetime.fromtimestamp(packet["ts"] / 1000)
        depth.datetime = dt
        tick_data = packet["tick"]
        if "bids" not in tick_data or "asks" not in tick_data:
            print(packet)
            return

        bids = tick_data["bids"]
        for n in range(DepthData.N_DEPTH):
            price, volume = bids[n]
            depth.bid_prices[n] = price
            depth.bid_volumes[n] = volume

        asks = tick_data["asks"]
        for n in range(DepthData.N_DEPTH):
            price, volume = asks[n]
            depth.ask_prices[n] = price
            depth.ask_volumes[n] = volume

    def _parse_bar(self, data, bar: BarData):
        bar.datetime = datetime.datetime.fromtimestamp(data["ts"] / 1000)
        tick_data = data["tick"]
        bar.open = tick_data['open']
        bar.high = tick_data['high']
        bar.low = tick_data['low']
        bar.close = tick_data['close']
        bar.volume = tick_data['vol']

    def on_data(self, packet):
        channel = packet.get("ch", None)
        if channel in self._callback_dict:
            callback = self._callback_dict[channel]
            callback(packet)
        else:
            logger.info('%s got unhandled message %s', self, packet)
