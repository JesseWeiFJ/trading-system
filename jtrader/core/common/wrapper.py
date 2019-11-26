import functools
import time
from copy import copy

from jtrader.core.common.log import logger
from jtrader.core.common.utils import format_function


def update_wrapper(wrapper, job_func):
    if hasattr(job_func, '__name__'):
        wrapper.__name__ = job_func.__name__
        if hasattr(job_func, 'im_class'):
            wrapper.im_class = job_func.im_class
        if hasattr(job_func, '__module__'):
            wrapper.__module__ = job_func.__module__


class RetryWrapper(object):
    def __init__(self, max_retry=2, exception=Exception, default_result=None, sleep=0.0, sleep_multiplier=1.0):
        self._max_retry = max_retry
        self._exception = exception
        self._sleep_seconds = sleep
        self._sleep_multiplier = sleep_multiplier
        self._default_result = default_result

    def __call__(self, job_func):
        @functools.wraps(job_func)
        def wrapper(*args, **kwargs):
            n_retry = 0
            sleep_seconds = self._sleep_seconds
            while True:
                try:
                    result = job_func(*args, **kwargs)
                    n_retry = 0
                    return result
                except self._exception as e:
                    logger.debug("error happened: %s", e)
                    if n_retry < self._max_retry:
                        n_retry += 1
                        logger.debug("retry no.%d for %s", n_retry, format_function(job_func, *args, **kwargs))
                        if sleep_seconds > 0:
                            logger.debug("sleep %d seconds", sleep_seconds)
                            time.sleep(sleep_seconds)
                            sleep_seconds *= self._sleep_multiplier
                        continue
                    else:
                        logger.exception(e)
                        logger.info("failed to execute %s",
                                    format_function(job_func, *args, **kwargs))
                        break
            return copy(self._default_result)

        update_wrapper(wrapper, job_func)
        return wrapper
