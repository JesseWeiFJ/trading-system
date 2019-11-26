#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib.parse

import urllib
import base64
import json
import hashlib
import hmac
from datetime import datetime
from threading import Lock
import typing
import pandas as pd
from jtrader.datatype import *
from jtrader.core.tools.client import Request, RestClient
from jtrader.core.common import logger

STATUS_HBDM2VT = {
    3: EnumOrderStatus.PENDING,
    4: EnumOrderStatus.PARTIAL_FILLED,
    5: EnumOrderStatus.CANCELLED,
    6: EnumOrderStatus.FILLED,
    7: EnumOrderStatus.CANCELLED,
}

ORDERTYPE_VT2HBDM = {
    EnumOrderType.MARKET: "opponent",
    EnumOrderType.LIMIT: "limit",
}
ORDERTYPE_HBDM2VT = {v: k for k, v in ORDERTYPE_VT2HBDM.items()}

ORDERTYPE_HBDM2VT[1] = EnumOrderType.LIMIT
ORDERTYPE_HBDM2VT[3] = EnumOrderType.MARKET
ORDERTYPE_HBDM2VT[4] = EnumOrderType.MARKET
ORDERTYPE_HBDM2VT[5] = EnumOrderType.STOP
ORDERTYPE_HBDM2VT[6] = EnumOrderType.LIMIT

DIRECTION_VT2HBDM = {
    EnumOrderDirection.BUY: "buy",
    EnumOrderDirection.SELL: "sell",
}
DIRECTION_HBDM2VT = {v: k for k, v in DIRECTION_VT2HBDM.items()}

OFFSET_VT2HBDM = {
    EnumOffSet.OPEN: "open",
    EnumOffSet.CLOSE: "close",
}
OFFSET_HBDM2VT = {v: k for k, v in OFFSET_VT2HBDM.items()}


class HbdmRestApi(RestClient):

    TAG = ExchangeAbbr.HBDM
    HOST = "https://api.hbdm.com"

    @staticmethod
    def create_signature(api_key, method, host, path, secret_key, get_params=None):
        sorted_params = [
            ("AccessKeyId", api_key),
            ("SignatureMethod", "HmacSHA256"),
            ("SignatureVersion", "2"),
            ("Timestamp", datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"))
        ]

        if get_params:
            sorted_params.extend(list(get_params.items()))
            sorted_params = list(sorted(sorted_params))
        encode_params = urllib.parse.urlencode(sorted_params)

        payload = [method, host, path, encode_params]
        payload = "\n".join(payload)
        payload = payload.encode(encoding="UTF8")

        secret_key = secret_key.encode(encoding="UTF8")

        digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(digest)

        params = dict(sorted_params)
        params["Signature"] = signature.decode("UTF8")
        return params

    def on_data(self, data):
        self._callback(data)

    on_bar = on_depth = on_order = on_trade = on_data

    def __init__(self):
        super().__init__()
        self.symbol_type_map = {}

        self.api_key = ""
        self.api_secret = ""

        self.url_base = self.HOST
        self.order_count = 10000
        self.order_count_lock = Lock()
        self.connect_time = 0

        self.positions = {}
        self.currencies = set()
        self.contracts: typing.Dict[str, ContractData] = {}

        self._callback: typing.Callable = print

    def set_callback(self, callback):
        self._callback = callback

    def sign(self, request):
        request.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/39.0.2171.71 Safari/537.36"
        }
        params_with_signature = self.create_signature(
            self.api_key,
            request.method,
            self.HOST,
            request.path,
            self.api_secret,
            request.params
        )
        request.params = params_with_signature

        if request.method == "POST":
            request.headers["Content-Type"] = "application/json"

            if request.data:
                request.data = json.dumps(request.data)

        return request

    def connect(self, api_key='', api_secret=''):
        self.api_key = api_key
        self.api_secret = api_secret
        self.fetch_contract()

    def fetch_balance(self):
        self.add_request(
            method="POST",
            path="/api/v1/contract_account_info",
            callback=self.on_query_account
        )

    def fetch_contract(self):
        self.add_request(
            method="GET",
            path="/api/v1/contract_contract_info",
            callback=self.on_query_contract
        )

    def send_order(self, req: OrderData):
        data = {
            "contract_code": req.symbol,
            "client_order_id": int(req.client_order_id),
            "price": req.price,
            "volume": int(req.volume),
            "direction": DIRECTION_VT2HBDM.get(req.direction, ""),
            # "offset": OFFSET_VT2HBDM.get(req.offset, ""),
            "offset": OFFSET_VT2HBDM.get(req.parameter.get('offset'), ""),
            "order_price_type": ORDERTYPE_VT2HBDM.get(req.order_type, ""),
            "lever_rate": 20
        }

        self.add_request(
            method="POST",
            path="/api/v1/contract_order",
            callback=self.on_send_order,
            data=data,
            extra=req,
            on_error=self.on_send_order_error,
            on_failed=self.on_send_order_failed
        )

    def cancel_order(self, req: OrderData):
        data = {
            "symbol": self.contracts[req.symbol].symbol_base,
            "order_id": req.order_id
        }

        self.add_request(
            method="POST",
            path="/api/v1/contract_cancel",
            callback=self.on_cancel_order,
            on_failed=self.on_cancel_order_failed,
            data=data,
            extra=req
        )

    def on_query_account(self, data, request):
        if self.check_error(data, "查询账户"):
            return
        account_list = []
        for d in data["data"]:
            account = dict(
                accountid=d["symbol"],
                balance=d["margin_balance"],
                frozen=d["margin_frozen"],
            )
            account_list.append(account)

        return pd.DataFrame(account_list)

    def on_query_contract(self, data, request):  # type: (dict, Request)->None
        for d in data["data"]:
            self.currencies.add(d["symbol"])
            contract = ContractData()
            contract.symbol_exchange = contract.symbol_root = d["contract_code"]
            contract.exchange = self.TAG
            contract.symbol = '.'.join([contract.symbol_root, contract.exchange])
            contract.tick_size = d["price_tick"]
            contract.lot_size = 1
            contract.multiplier = int(d["contract_size"])
            # contract.contract_type = EnumContractType.FUTURES
            contract.contract_type = ContractTypeAbbr.FUTURES

            contract.symbol_base = d["symbol"]
            contract.symbol_quote = 'USD'
            contract.asset_base = '.'.join([contract.symbol_base, contract.exchange])
            contract.asset_quote = '.'.join([contract.symbol_quote, contract.exchange])

            self.symbol_type_map[contract.symbol] = d["contract_type"]
            self.contracts[contract.symbol] = contract

    def on_send_order(self, data, request):
        """"""
        order = request.extra

        if self.check_error(data, "委托"):
            order.status = EnumOrderStatus.REJECTED
            self.on_order(order)

    def on_send_order_failed(self, status_code: str, request: Request):
        """
        Callback when sending order failed on server.
        """
        order = request.extra
        order.status = EnumOrderStatus.REJECTED
        self.on_order(order)

        msg = f"委托失败，状态码：{status_code}，信息：{request.response.text}"
        logger.info(msg)

    def on_send_order_error(
            self, exception_type: type, exception_value: Exception, tb, request: Request
    ):
        """
        Callback when sending order caused exception.
        """
        order = request.extra
        order.status = EnumOrderStatus.REJECTED
        self.on_order(order)

        # Record exception if not ConnectionError
        if not issubclass(exception_type, ConnectionError):
            self.on_error(exception_type, exception_value, tb, request)

    def on_cancel_order(self, data, request):
        """"""
        self.check_error(data, "撤单")

    def on_cancel_order_failed(self, status_code: str, request: Request):
        msg = f"撤单失败，状态码：{status_code}，信息：{request.response.text}"
        logger.info(msg)

    def on_error(
            self, exception_type: type, exception_value: Exception, tb, request: Request
    ):
        msg = f"触发异常，状态码：{exception_type}，信息：{exception_value}"
        logger.error(msg)

    def check_error(self, data: dict, func: str = ""):
        if data["status"] != "error":
            return False

        error_code = data["err_code"]
        error_msg = data["err_msg"]
        logger.error(f"{func}请求出错，代码：{error_code}，信息：{error_msg}")
        return True

    def back_fill_bars(self, *args, **kwargs):
        return []

