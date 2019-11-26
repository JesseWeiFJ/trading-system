#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import json
import zlib
import time
from jtrader.core.common import logger

from jtrader.core.tools.client import WebsocketClient
from jtrader.broker.gateway.hbdm_gateway.rest_api import HbdmRestApi


def _split_url(url):
    result = re.match("\w+://([^/]*)(.*)", url)  # noqa
    if result:
        return result.group(1), result.group(2)


class HBDMStreamMixin(object):

    def login(self):
        """"""
        host, path = _split_url(self.HOST)
        params = {
            "op": "auth",
            "type": "api",
            "cid": str(time.time()),
        }
        params.update(
            self.api.create_signature(
                self.api.api_key, "GET", host, path, self.api.api_secret
            )
        )
        return self.send_packet(params)

    @staticmethod
    def unpack_data(data):
        return json.loads(zlib.decompress(data, 31))

    def on_connected(self):
        self.login()
        super(HBDMStreamMixin, self).on_connected()

    def on_packet(self, packet):
        if "ping" in packet:
            req = {"pong": packet["ping"]}
            self.send_packet(req)
        elif "op" in packet and packet["op"] == "ping":
            req = {
                "op": "pong",
                "ts": packet["ts"]
            }
            self.send_packet(req)
        elif "err-msg" in packet:
            code = packet["err-code"]
            msg = packet["err-msg"]
            logger.warning(f'{self} got error code {code} with message {msg}')
        elif "op" in packet and packet["op"] == "auth":
            logger.info(f'{self} connected')
        else:
            self.on_data(packet)
        """"""

    def on_data(self, packet):
        """"""
        print("data : {}".format(packet))
