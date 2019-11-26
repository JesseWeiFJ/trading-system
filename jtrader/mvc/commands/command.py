#!/usr/bin/env python
# -*- coding: utf-8 -*-
from jtrader.datatype.base import *
from jtrader.datatype.enums import EnumEventType
from jtrader.mvc.views import Viewer


@dataclass
class CommandBaseData(BaseData):
    EVENT_TYPE = EnumEventType.COMMAND
    ACTOR = ''

    def split(self, cmd_str: str):
        return cmd_str.split()

    def parse(self, cmd_str: str):
        pass

    def execute(self, actor):
        pass

    def __init__(self):
        super(CommandBaseData, self).__init__()
        self._viewer: Viewer = None

    def set_viewer(self, viewer):
        self._viewer = viewer

    def render(self, status):
        self._viewer.render(status)
