#!/usr/bin/env python
# -*- coding: utf-8 -*-
from jtrader.mvc.views.view import Viewer


class ConsoleViewer(Viewer):
    TAG = 'console'

    def render(self, msg):
        print(msg)
