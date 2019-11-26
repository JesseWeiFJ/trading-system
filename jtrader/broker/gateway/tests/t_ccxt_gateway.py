
from jtrader.broker.gateway.binance_gateway import BinanceGateway as GW
# from jtrader.broker.gateway import FCoinGateway as GW
import datetime

gateway = GW()
gateway_config = {
    'api_key': '',
    'api_secret': '',
    "symbol": [
        "ETH/USDT.BNC",
        # "ETH/USDT.FC",
    ],
    "frequency": [
        "1m",
    ],
    "depth_flag": True,
}


def callback(data):
    # print(data.pretty_string())
    # print(datetime.datetime.utcnow())
    print(data)
    # print()


gateway.set_callback(callback)
gateway.configure(gateway_config)
gateway.start()

import time
print('sleep 10s')
print('sleep 10s')
print('sleep 10s')
time.sleep(10)
gateway.stop()

#
# #
# def process_message(msg):
#     print("message type: {}".format(msg['e']))
#     print(msg)
#
# # process_message = gateway.agg_ws_api._on_bar_impl('BNB/BTC.BNC', '1m')
#
# from binance.client import Client
# client = Client('', '')
# from binance.websockets import BinanceSocketManager
# bm = BinanceSocketManager(client)
#
# from binance.enums import *
# conn_key = bm.start_kline_socket('BNBBTC', process_message, interval=KLINE_INTERVAL_1MINUTE)
# # conn_key = bm.start_depth_socket('BNBBTC', process_message)
#
# bm.start()
#
# bm.close()
#
#
# gateway.agg_ws_api._bar_dict