#!/usr/bin/env python
# -*- coding: utf-8 -*-
import traceback
# import signal
import zmq
import msgpack
from threading import Thread
# signal.signal(signal.SIGINT, signal.SIG_DFL)


class Engine(object):

    def __init__(self):
        super(Engine, self).__init__()
        self._thd = Thread()
        self._active = False

    @property
    def active(self):
        return self._active

    def run(self):
        pass

    def start(self):
        self._active = True
        if not self._thd.isAlive():
            self._thd = Thread(target=self.run)
            self._thd.start()

    def stop(self):
        self._active = False
        if self._thd.isAlive():
            self._thd.join()


class RpcParty(Engine):
    def pack(self, data):
        return msgpack.packb(data)

    def unpack(self, data):
        return msgpack.unpackb(data)

    def encode(self, string: str):
        return string.encode('utf-8')

    def decode(self, byte: bytes):
        return byte.decode('utf-8')


class RemoteException(Exception):
    def __init__(self, value):
        self.__value = value

    def __str__(self):
        return self.__value


class RpcServer(RpcParty):
    def __init__(self, reply_address, publish_address):
        super(RpcServer, self).__init__()
        self._function_dict = {}

        self._context = zmq.Context()

        self._socket_reply = self._context.socket(zmq.REP)
        self._socket_reply.bind(reply_address)

        self._socket_publish = self._context.socket(zmq.PUB)
        self._socket_publish.bind(publish_address)

    def run(self):
        while self.active:
            if not self._socket_reply.poll(1000):
                continue

            req_binary = self._socket_reply.recv()
            name, args, kwargs = self.unpack(req_binary)

            try:
                func = getattr(self, self.decode(name))
                r = func(*args, **kwargs)
                rep = [True, r]
            except Exception as e:
                rep = [False, traceback.format_exc()]

            rep_binary = self.pack(rep)
            self._socket_reply.send(rep_binary)

    def publish(self, topic, data):
        if isinstance(topic, str):
            topic = self.encode(topic)
        datab = self.pack(data)
        self._socket_publish.send_multipart([topic, datab])


class RpcClient(RpcParty):
    TOPICS = []

    def __init__(self, request_address, subscribe_address):
        super(RpcClient, self).__init__()

        self._request_address = request_address
        self._subscribe_address = subscribe_address

        self._context = zmq.Context()
        self._socket_request = self._context.socket(zmq.REQ)
        self._socket_subscribe = self._context.socket(zmq.SUB)
        
        self._socket_request.connect(self._request_address)
        self._socket_subscribe.connect(self._subscribe_address)

        self._callback_dict = {}

        for topic in self.TOPICS:
            self.subscribe_topic(topic)

    def __getattr__(self, name):
        def do_rpc(*args, **kwargs):
            req = [name, args, kwargs]

            req_binary = self.pack(req)
            self._socket_request.send(req_binary)
            rep_binary = self._socket_request.recv()
            rep = self.unpack(rep_binary)
            if rep[0]:
                return rep[1]
            else:
                raise RemoteException(rep[1])
        return do_rpc
    
    def run(self):
        while self.active:
            if not self._socket_subscribe.poll(1000):
                continue

            topic, datab = self._socket_subscribe.recv_multipart()
            data = self.unpack(datab)

            func = self._callback_dict[self.decode(topic)]
            try:
                func(data)
            except Exception as e:
                print(traceback.format_exc())
                print('Failed to handle %s(%s)' % (func, data))

    def subscribe_topic(self, topic):
        func = getattr(self, topic)
        self._callback_dict[topic] = func
        topic = topic.encode('utf-8')
        self._socket_subscribe.setsockopt(zmq.SUBSCRIBE, topic)
