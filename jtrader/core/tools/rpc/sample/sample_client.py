#!/usr/bin/env python
# -*- coding: utf-8 -*-
from time import sleep
from jtrader.core.tools.rpc import RpcClient


class LocalClient(RpcClient):
    TOPICS = ['test']

    def test(self, data):
        print('client received topic test with data:', data)


if __name__ == '__main__':

    publish_address = 'ipc:///tmp/zerorpc_test_socket_4241.sock'
    reply_address = 'ipc:///tmp/zerorpc_test_socket_4242.sock'

    tc = LocalClient(reply_address, publish_address)
    tc.start()

    req = ['add', (1, 3), {}]
    req_binary = tc.pack(req)
    tc._socket_request.send(req_binary)
    tc._socket_request.poll(timeout=0)
    rep_binary = tc._socket_request.recv(1)
    rep = tc.unpack(rep_binary)
    print(rep)

    while 1:
        print(tc.add(1, 3))
        sleep(2)
