#!/usr/bin/env python
# -*- coding: utf-8 -*-

import typing

from jtrader.core.tools.scheduler.scheduler import BusyScheduler
from jtrader.core.tools.scheduler.job import DelayJob, OneOffJob, OnTimeJob
from jtrader.datatype import *
from jtrader.core.common import Singleton, Subject


class Timer(BusyScheduler, Subject):

    def __init__(self):
        super(Timer, self).__init__()

        job = DelayJob('1s', self._on_heartbeat, '1s')
        self.add_job(job)
        job = OneOffJob('0s', self._on_heartbeat, '1s')
        self.add_job(job)

        for frequency in ['1m', '15m', '30m', '1h']:
            if frequency not in TIME_INTERVAL_MAP:
                raise TypeError(f'Invalid time frequency {frequency}')
            job = OnTimeJob(frequency, self._on_heartbeat, frequency)
            self.add_job(job)

    def _on_heartbeat(self, frequency='1s'):
        heartbeat = HeartBeatData()
        heartbeat.frequency = frequency
        self.notify(EnumEventType.HEARTBEAT, heartbeat)

