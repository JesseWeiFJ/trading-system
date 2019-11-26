from jtrader.broker.gateway.websocket_api import AggregateWebsocketApi
from jtrader.datatype import *
from jtrader.core.common import logger

from binance.client import Client
from binance.websockets import BinanceSocketManager
import binance.enums
import datetime
import typing
import copy

STATUS_MAP_REVERSE = dict()
STATUS_MAP_REVERSE['NEW'] = EnumOrderStatus.PENDING
STATUS_MAP_REVERSE['PARTIALLY_FILLED'] = EnumOrderStatus.PARTIAL_FILLED
STATUS_MAP_REVERSE['FILLED'] = EnumOrderStatus.FILLED
STATUS_MAP_REVERSE['CANCELED'] = EnumOrderStatus.PARTIAL_FILLED
STATUS_MAP_REVERSE['REJECTED'] = EnumOrderStatus.ERROR
STATUS_MAP_REVERSE['EXPIRED'] = EnumOrderStatus.ERROR


class BinanceStream(AggregateWebsocketApi):
    TAG = ExchangeAbbr.BINANCE

    def __init__(self, api):
        super(BinanceStream, self).__init__(api)
        self._socket_manager: BinanceSocketManager = None

    def subscribe_bar(self, symbol, frequency):
        symbol_exchange = self.api.contracts[symbol].symbol_exchange
        self._socket_manager.start_kline_socket(symbol_exchange, self._on_bar_impl(symbol, frequency), frequency)

    def subscribe_depth(self, symbol):
        symbol_exchange = self.api.contracts[symbol].symbol_exchange
        self._socket_manager.start_depth_socket(symbol_exchange,
                                                self._on_depth_impl(symbol),
                                                binance.enums.WEBSOCKET_DEPTH_5)

    def _on_bar_impl(self, symbol, frequency):
        bar = BarData()
        bar.symbol = symbol
        bar.frequency = frequency
        bar.datetime = None
        self._bar_dict[(symbol, frequency)] = bar

        def callback(packet):
            origin_dt = bar.datetime
            kline = packet['k']
            dt = datetime.datetime.utcfromtimestamp(kline['t'] / 1000.0)
            if origin_dt is not None and dt > origin_dt:
                self.api.on_bar(copy.copy(bar))
            self._parse_bar(packet, bar)
            bar.datetime = dt

        return callback

    def _parse_bar(self, packet, bar: BarData):
        kline = packet['k']
        bar.open = float(kline['o'])
        bar.high = float(kline['h'])
        bar.low = float(kline['l'])
        bar.close = float(kline['c'])
        bar.volume = float(kline['v'])

    def _parse_depth(self, packet, depth: DepthData):
        depth.datetime = datetime.datetime.utcnow()
        bids = packet['bids']
        for index, (price, volume) in enumerate(bids[:DepthData.N_DEPTH]):
            depth.bid_prices[index] = float(price)
            depth.bid_volumes[index] = float(volume)
        asks = packet['asks']
        for index, (price, volume) in enumerate(asks[:DepthData.N_DEPTH]):
            depth.ask_prices[index] = float(price)
            depth.ask_volumes[index] = float(volume)

    def start(self):
        self._socket_manager = BinanceSocketManager(Client(self.api.api_key, self.api.api_secret))
        self.on_connected()
        self.back_fill()
        self._socket_manager.start()

    def stop(self):
        self._socket_manager.close()
        import twisted.internet.error
        from twisted.internet import reactor
        try:
            reactor.stop()
        except twisted.internet.error.ReactorNotRunning:
            pass

    def subscribe_user_stream(self):
        self._socket_manager.start_user_socket(self.on_user_stream)

    def on_user_stream(self, data):
        if data['e'] == 'executionReport':
            logger.debug(f'{self} received raw data {data}')
            if data['C'] != 'null':
                cli_id = data['C']
            else:
                cli_id = data['c']

            order = self.api.oms.clone(cli_id)
            if order is None:
                return

            order.order_id = str(data['i'])
            order.executed_volume = float(data['z'])
            order.executed_notional = float(data['Z'])
            order.status = STATUS_MAP_REVERSE[data['X']]

            if float(data['l']):
                trade = TradeData.from_order(order)
                trade.trade_id = str(data['t'])
                trade.price = float(data['L'])
                trade.volume = float(data['l'])
                trade.commission = float(data['n'])
                trade.commission_asset = '.'.join((data['N'], self.TAG))
                trade.datetime = datetime.datetime.utcfromtimestamp(data['E'] / 1000.0)
                trade.strategy_id = order.strategy_id
                trade.client_order_id = order.client_order_id

                contract = trade.contract
                if trade.commission != 0 and trade.commission_asset == 'BNB.BNC':
                    if (trade.commission_asset != contract.asset_base) and \
                            (trade.commission_asset != contract.asset_quote):

                        commission_trade = trade.copy()
                        commission_trade.commission = 0.0
                        commission_trade.symbol = 'BNB' + contract.symbol_quote + '.BNC'
                        commission_trade.direction = EnumOrderDirection.SELL

                        notional = trade.volume * trade.price * 0.00075
                        commission_trade.price = notional / trade.commission
                        commission_trade.volume = notional / commission_trade.price
                        commission_trade.trade_id = generate_id()
                        self.api.on_trade(commission_trade)

                        trade.commission_asset = contract.asset_quote
                        trade.commission = notional

                self.api.on_trade(trade)
                logger.debug("%s: receive %s", self, trade)

            self.api.on_order(order)
            if order.is_closed():
                self.api.oms.pop(order.client_order_id)

            logger.debug("%s: receive %s", self, order)
