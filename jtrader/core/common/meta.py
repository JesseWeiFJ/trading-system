#!/usr/bin/env python
# -*- coding: utf-8 -*-
import weakref
import threading


class Singleton(type):
    def __init__(cls, name, bases, attrs):
        super(Singleton, cls).__init__(name, bases, attrs)
        cls._instance = None
        cls._lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instance


class Cached(type):
    def __init__(cls, *args, **kwargs):
        super(Cached, cls).__init__(*args, **kwargs)
        cls._cache = weakref.WeakValueDictionary()
        cls._lock = threading.Lock()

    def __call__(cls, *args):
        if args not in cls._cache:
            with cls._lock:
                if args not in cls._cache:
                    obj = super(Cached, cls).__call__(*args)
                    cls._cache[args] = obj
        return cls._cache[args]

