#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging.handlers
import logging
from queue import Queue
import threading
import os
import datetime

from jtrader.core.common.context import LimitedQueryContext

_email_context = LimitedQueryContext(10, '1h')


class AsyncHandlerMixin(object):
    def __init__(self, *args, **kwargs):
        super(AsyncHandlerMixin, self).__init__(*args, **kwargs)
        self.__queue = Queue()
        self.__thread = threading.Thread(target=self.__loop)
        self.__thread.daemon = True
        self.__thread.start()

    def emit(self, record):
        self.__queue.put(record)

    def __loop(self):
        while True:
            record = self.__queue.get()
            try:
                super(AsyncHandlerMixin, self).emit(record)
            except:
                pass


class AsyncRotatingFileHandler(AsyncHandlerMixin, logging.handlers.RotatingFileHandler):
    pass


class AdvancedRotatingFileHandler(logging.handlers.RotatingFileHandler):
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=False):
        head, tail = os.path.split(filename)
        tail = datetime.datetime.now().strftime(tail)

        if not os.path.exists(head):
            os.mkdir(head)

        filename = os.path.join(head, tail)
        super(AdvancedRotatingFileHandler, self).__init__(filename, mode, maxBytes, backupCount, encoding, delay)



class TlsSMTPHandler(logging.handlers.SMTPHandler):

    def _send_email(self, record):
        try:
            import smtplib
            from email.utils import formatdate
            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT
            smtp = smtplib.SMTP(self.mailhost, port)
            msg = self.format(record)
            msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\nDate: %s\r\n\r\n%s" % (
                self.fromaddr,
                ",".join(self.toaddrs),
                self.getSubject(record),
                formatdate(), msg)
            if self.username:
                smtp.ehlo()  # for tls add this line
                smtp.starttls()  # for tls add this line
                smtp.ehlo()  # for tls add this line
                smtp.login(self.username, self.password)
            smtp.sendmail(self.fromaddr, self.toaddrs, msg)
            smtp.quit()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def emit(self, record):
        """
        Emit a record.

        Format the record and send it to the specified addressees.
        """
        # self._send_email(record)
        if _email_context.has_token():
            t = threading.Thread(target=self._send_email, args=(record,))
            t.start()
            _email_context.add_count()
        else:
            pass


DEFAULT_LOG_FORMATTER = logging.Formatter(fmt='%(asctime)s.%(msecs)03d [%(levelname)s][%(threadName)s] %(message)s',
                                          datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger('jtrader')

logger.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(DEFAULT_LOG_FORMATTER)
logger.addHandler(handler)
