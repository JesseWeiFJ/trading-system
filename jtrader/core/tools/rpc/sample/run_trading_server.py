#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from jtrader.mvc.control import ControlShell
from jtrader.core.tools.rpc import RpcServer
import pandas as pd

pd.options.display.float_format = '{:.6f}'.format


class RemoteController(RpcServer):

    def __init__(self, reply_address, publish_address):
        super(RemoteController, self).__init__(reply_address, publish_address)
        self._controller: ControlShell = None

    def _viewer_func(self, status):
        self.publish('status', status)

    def set_controller(self, controller: ControlShell):
        self._controller = controller

    def command(self, cmd_line):
        self._controller.set_viewer(self._viewer_func)
        self._controller.onecmd(self.decode(cmd_line))
        self._controller.set_viewer(print)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = r'etc/real_time_trading.json'

    control = ControlShell()
    control.configure(config_path)
    control.do_start('')

    publish_address = 'ipc:///tmp/zerorpc_test_socket_4241.sock'
    reply_address = 'ipc:///tmp/zerorpc_test_socket_4242.sock'

    rpc_server = RemoteController(reply_address, publish_address)
    rpc_server.set_controller(control)

    rpc_server.start()
    control.cmdloop()
    rpc_server.stop()
