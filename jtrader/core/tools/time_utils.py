#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd
import datetime


class TimeUtils(object):

    @staticmethod
    def _round_time(dt=None, date_delta=datetime.timedelta(minutes=1), to='round'):
        round_to = date_delta.total_seconds()
        if dt is None:
            dt = datetime.datetime.now()
        seconds = (dt - dt.min).seconds

        if to == 'ceil':
            rounding = (seconds + round_to) // round_to * round_to
        elif to == 'floor':
            rounding = seconds // round_to * round_to
        else:
            rounding = (seconds + round_to / 2) // round_to * round_to
        return dt + datetime.timedelta(0, rounding - seconds, -dt.microsecond)

    @staticmethod
    def floor_time(dt=None, date_delta=datetime.timedelta(minutes=1)):
        return TimeUtils._round_time(dt, date_delta, 'floor')

    @staticmethod
    def ceil_time(dt=None, date_delta=datetime.timedelta(minutes=1)):
        return TimeUtils._round_time(dt, date_delta, 'ceil')

    @staticmethod
    def round_time(dt=None, date_delta=datetime.timedelta(minutes=1)):
        return TimeUtils._round_time(dt, date_delta, 'round')


if __name__ == '__main__':
    date = pd.datetime(2012, 2, 12, 15, 40, 13, 598763)
    delta1 = pd.to_timedelta('1s')
    delta2 = pd.to_timedelta('1m')
    delta3 = pd.to_timedelta('1d')

    TimeUtils.floor_time(date, delta2)
    TimeUtils.floor_time(date, -delta2)
    TimeUtils.floor_time(date, delta1)
    TimeUtils.ceil_time(date, delta1)
    TimeUtils.floor_time(date, delta3)
