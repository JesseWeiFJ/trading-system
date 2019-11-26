import json
import ssl
import socket
from datetime import datetime
from threading import Lock, Thread
from time import sleep

import websocket

from scikit_backtest.core import logger


class WebsocketClient(object):
    HOST = ''
    HEADER = {}

    PROXY_HOST = None
    PROXY_PORT = None
    
    def __init__(self):
        
        self._ws_lock = Lock()
        self._ws = websocket.WebSocket()

        self._worker_thread = None
        self._ping_thread = None
        self._active = False

        self._ping_interval = 60     # seconds

    def start(self):
        self._active = True
        self._worker_thread = Thread(target=self._run)
        self._worker_thread.start()

        self._ping_thread = Thread(target=self._run_ping)
        self._ping_thread.start()

    def stop(self):
        self._active = False
        self._disconnect()

    def join(self):
        self._ping_thread.join()
        self._worker_thread.join()

    def send_packet(self, packet: dict):
        text = json.dumps(packet)
        return self._send_text(text)

    def _send_text(self, text: str):
        ws = self._ws
        if ws:
            ws.send(text, opcode=websocket.ABNF.OPCODE_TEXT)

    def _ensure_connection(self):
        triggered = False
        with self._ws_lock:
            if self._ws is None:
                self._ws = websocket.create_connection(
                    self.HOST,
                    sslopt={"cert_reqs": ssl.CERT_NONE},
                    http_proxy_host=self.PROXY_HOST,
                    http_proxy_port=self.PROXY_PORT,
                    header=self.HEADER
                )
                triggered = True
        if triggered:
            self.on_connected()

    def _disconnect(self):
        triggered = False
        with self._ws_lock:
            if self._ws:
                ws: websocket.WebSocket = self._ws
                self._ws = None

                triggered = True
        if triggered:
            ws.close()
            self.on_disconnected()

    def _run(self):
        try:
            while self._active:
                try:
                    self._ensure_connection()
                    ws = self._ws
                    if ws:
                        text = ws.recv()

                        # ws object is closed when recv function is blocking
                        if not text:
                            self._disconnect()
                            continue

                        try:
                            data = self.unpack_data(text)
                        except ValueError as e:
                            print("websocket unable to parse data: " + text)
                            raise e

                        self.on_packet(data)
                # ws is closed before recv function is called
                # For socket.error, see Issue #1608
                except (websocket.WebSocketConnectionClosedException, socket.error):
                    self._disconnect()

                # other internal exception raised in on_packet
                except Exception as e:  # noqa
                    logger.exception(e)
                    self._disconnect()
        except Exception as e:  # noqa
            logger.exception(e)
        self._disconnect()

    @staticmethod
    def unpack_data(data: str):
        return json.loads(data)

    def _run_ping(self):
        """"""
        while self._active:
            try:
                self._ping()
            except Exception as e:
                logger.exception(e)
                sleep(1)

            for i in range(self._ping_interval):
                if not self._active:
                    break
                sleep(1)

    def _ping(self):
        """"""
        ws = self._ws
        if ws:
            ws.send("ping", websocket.ABNF.OPCODE_PING)

    def on_connected(self):
        pass

    def on_disconnected(self):
        pass

    def on_packet(self, packet: dict):
        pass
