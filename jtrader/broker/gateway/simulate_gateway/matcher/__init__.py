#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .matcher import Matcher
from .simple_matcher import SimpleMatcher
from .cross_matcher import CrossMatcher


class MatcherFactory(object):
    def __new__(cls, name) -> Matcher:
        _instance = Matcher.factory_create(name)
        return _instance
