#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import deque
import threading
import pandas as pd
import time
import logging

logger = logging.getLogger('jtrader')


class LimitedQueryContext(object):
    """
    A context management limiting query times within a given time window.
    """
    def __init__(self, n_query, duration_unit='1s', action=None):
        """
        Constructor of context manager for limiting query
        :param n_query: number of
        :param duration_unit: time window of query time
        """
        self._n_second_duration = 0.0
        self._n_max_query = 0.0
        self._time_deque = deque()
        self._action = action

        self._lock = threading.Lock()
        self.reset(n_query, duration_unit)

    def reset(self, n_query, duration_unit='1s'):
        if not isinstance(n_query, int):
            raise TypeError("n_query should be type int")
        if n_query <= 0:
            raise TypeError("n_query should be greater than 0")

        with self._lock:
            self._time_deque = deque(maxlen=n_query)
            self._n_max_query = n_query
            self._n_second_duration = pd.to_timedelta(duration_unit).total_seconds()

    def has_token(self):
        now = time.time()
        if len(self._time_deque) != self._n_max_query:
            return True
        else:
            first_time = self._time_deque[0]
            if now - first_time > self._n_second_duration:
                return True
            else:
                return False

    def add_count(self):
        self._time_deque.append(time.time())

    def __enter__(self):
        with self._lock:
            if not self.has_token():
                sleep_time = self._time_deque[0] + self._n_second_duration - time.time()
                if self._action is None:
                    logger.debug("Sleep %f seconds before query", sleep_time, )
                    time.sleep(sleep_time)
                else:
                    self._action()
            self.add_count()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
