import datetime
import time

from jtrader.core.tools.scheduler.job import CancelJob
from jtrader.core.common import logger, Engine


class Scheduler(Engine):
    clock_func = datetime.datetime.now

    def __init__(self):
        super(Scheduler, self).__init__()
        self._jobs = []

    def _run_job(self, job):
        ret = job.run()
        if isinstance(ret, CancelJob) or ret is CancelJob:
            self.cancel_job(job)
        else:
            job.schedule_next_run(self.clock_func())

    def set_clock_func(self, clock_func):
        self.clock_func = clock_func

    def run_pending(self, dt=None):
        if len(self._jobs):
            if dt is None:
                dt = self.clock_func()
            runnable_jobs = (job for job in self._jobs if job.should_run(dt))
            for job in runnable_jobs:
                self._run_job(job)

    def schedule_all(self):
        for job in self._jobs:
            job.schedule_next_run(self.clock_func())

    def run_all(self):
        for job in self._jobs:
            self._run_job(job)

    def idle_time(self):
        next_run_time = min(job.next_run_time() for job in self._jobs)
        now = self.clock_func()
        if next_run_time < now:
            return now - next_run_time
        else:
            return datetime.timedelta(0)

    def cancel_job(self, job):
        try:
            self._jobs.remove(job)
        except ValueError:
            pass

    def cancel_all(self):
        self._jobs = []

    def add_job(self, job):
        job.schedule_next_run(self.clock_func())
        self._jobs.append(job)

    def run(self):
        try:
            while self.active:
                self._process_jobs()
        except KeyboardInterrupt:
            logger.info('KeyboardInterrupt Caught!!')
        except Exception as e:
            logger.exception(e)

    def _process_jobs(self):
        raise NotImplementedError


class BusyScheduler(Scheduler):
    def __init__(self, interval_time=1):
        super(BusyScheduler, self).__init__()
        self._interval_time = interval_time

    def _process_jobs(self):
        self.run_pending()
        time.sleep(self._interval_time)


class LazyScheduler(Scheduler):

    def _process_jobs(self):
        self.run_pending()
        time.sleep(self.idle_time().total_seconds())
