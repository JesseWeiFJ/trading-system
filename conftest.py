#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pytest import fixture
from jtrader.core.common import logger


@fixture(scope='session')
def silence_logger():
    logger.disabled = True
    yield
    logger.disabled = False
