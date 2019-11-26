#!/usr/bin/env python
# -*- coding: utf-8 -*-
from time import sleep, time
from jtrader.core.tools.rpc import RpcServer


class RemoteServer(RpcServer):
    def add(self, a, b):
        print('receiving: %s, %s' % (a,b))
        return a + b


if __name__ == '__main__':

    publish_address = 'ipc:///tmp/zerorpc_test_socket_4241.sock'
    reply_address = 'ipc:///tmp/zerorpc_test_socket_4242.sock'

    ts = RemoteServer(reply_address, publish_address)
    ts.start()

    while 1:
        content = 'current server time is %s' % time()
        print(content)
        ts.publish('test', content)
        sleep(2)
