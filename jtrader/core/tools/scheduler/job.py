#!/usr/bin/env python
# -*- coding: utf-8 -*-
import collections
import datetime
import pandas as pd

from jtrader.core.common import logger, format_function


class CancelJob(object):
    pass


class Job(object):

    def __repr__(self):
        call_repr = format_function(self._job_func, *self._args, **self._kwargs)
        return '{job_type} of {job_info}'.format(
            job_type=self.__class__.__name__, job_info=call_repr
        )

    def __lt__(self, other):
        return self.next_run_time() < other.next_run_time()

    def next_run_time(self):
        return self._next_run

    def should_run(self, dt):
        return dt >= self._next_run

    def run(self):
        ret = self._job_func(*self._args, **self._kwargs)
        return ret

    def schedule_next_run(self, dt):
        raise NotImplementedError

    def __init__(self, job_func, *args, **kwargs):
        self._next_run: datetime = None
        self._job_func = job_func
        self._args = args
        self._kwargs = kwargs


class OnTimeJob(Job):
    def __init__(self, schedule_time, job_func, *args, **kwargs):
        super(OnTimeJob, self).__init__(job_func, *args, **kwargs)
        if isinstance(schedule_time, (list, tuple)):
            if len(schedule_time) == 0:
                raise TypeError("Empty list is not allowed")
            dts = pd.to_datetime(schedule_time).sort_values()
        elif isinstance(schedule_time, str):
            freq = pd.to_timedelta(schedule_time)
            n = int(datetime.timedelta(days=1).total_seconds() / freq.total_seconds())
            today_time = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
            dts = [today_time + i * freq for i in range(n)]
        else:
            raise TypeError("Expect string or list of string, got %s instead", type(schedule_time))
        self._time_deque = collections.deque(maxlen=len(dts))
        self._time_deque.extend(dts)

    def schedule_next_run(self, dt):
        delta = datetime.timedelta(days=1)
        while True:
            self._next_run = self._time_deque[0]
            if self._next_run <= dt:
                self._time_deque.append(self._next_run + delta)
            else:
                break


class DelayJob(Job):
    def __init__(self, freq, job_func, *args, **kwargs):
        super(DelayJob, self).__init__(job_func, *args, **kwargs)
        self._delay_time = pd.to_timedelta(freq)

    def schedule_next_run(self, dt):
        self._next_run = dt + self._delay_time


class OneOffJob(DelayJob):
    def run(self):
        super(OneOffJob, self).run()
        return CancelJob


class ExceptionCatchFunctor(object):
    def __init__(self, job_func, cancel_on_exception=False):
        self.job_func = job_func
        self.cancel_on_exception = cancel_on_exception

    def __call__(self, *args, **kwargs):
        try:
            return self.job_func(*args, **kwargs)
        except Exception as e:
            logger.exception(e)
            logger.info(f'Error happen when trigger {self.job_func} with params {args} and {kwargs}')
            if self.cancel_on_exception:
                return CancelJob

    def __repr__(self):
        return format_function(self.job_func)[:-2]
