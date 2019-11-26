#!/usr/bin/env python
# # -*- coding: utf-8 -*-
from jtrader.core.tools.rpc import RpcClient


class TradingClient(RpcClient):
    TOPICS = ['status']

    def status(self, status):
        print(self.decode(status))


if __name__ == '__main__':

    publish_address = 'ipc:///tmp/zerorpc_test_socket_4241.sock'
    reply_address = 'ipc:///tmp/zerorpc_test_socket_4242.sock'

    rpc_client = TradingClient(reply_address, publish_address)
    rpc_client.start()

    try:
        while True:
            cmd_line = input('JTrader: ')
            if cmd_line:
                rpc_client.command(cmd_line)
            if cmd_line == 'exit':
                break
    except KeyboardInterrupt:
        print('Catched KeyboardInterrupt!')
    except Exception as e:
        print(e)

    rpc_client.stop()
