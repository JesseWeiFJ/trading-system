#!/usr/bin/env python
# -*- coding: utf-8 -*-
from queue import Queue
from threading import Thread
from collections import defaultdict
import warnings
import typing
import ast
from sklearn.base import BaseEstimator as _BaseEstimator

from jtrader.core.common.log import logger
from jtrader.core.common.utils import parse_file


__all__ = [
    'Actor',
    'Subject',
    'Subscriber',
    'Observable',
    'Observer',
    'Engine',
    'LazyObject',
    'Registered',
    'Configurable'
]


class Configurable(_BaseEstimator):

    def reconfigure(self, new_config=None):
        # handle config from command line
        if new_config is None:
            config_dict = {}
            while True:
                key = input('Please input the key name(\\n for break): ')
                key = key.strip()
                if key:
                    value = input('Please input the value for key "{}": '.format(key))
                    value = ast.literal_eval(value)
                    config_dict[key] = value
                else:
                    break

        elif isinstance(new_config, str):
            config_dict = parse_file(new_config)
        elif isinstance(new_config, dict):
            config_dict = new_config
        else:
            raise TypeError('Not a proper config was passed, got "{}" instead'.format(new_config))

        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise TypeError('Invalid parameter "{}" for {}'.format(key, self))
        # self.set_params(**config_dict)


class ActorExit(Exception):
    pass


class Actor(object):
    def __init__(self):
        super(Actor, self).__init__()
        self._thread = Thread()
        self._queue = Queue()

    def send(self, msg):
        self._queue.put(msg)

    def _receive(self):
        msg = self._queue.get()
        if msg is ActorExit:
            raise ActorExit()
        return msg

    def handle_message(self, msg):
        pass

    def stop(self):
        if self._thread.is_alive():
            self._queue.put(ActorExit)
            self._thread.join()
            logger.debug('%s stopped', self.__class__.__name__)

    def start(self):
        if not self._thread.is_alive():
            self._thread = Thread(target=self._bootstrap)
            self._thread.start()
            logger.debug('%s started', self.__class__.__name__)

    def _bootstrap(self):
        try:
            self.run()
        except ActorExit:
            pass

    def run(self):
        while True:
            msg = self._receive()
            self.handle_message(msg)


class Subject(object):
    def __init__(self):
        super(Subject, self).__init__()
        self._handler_dict = defaultdict(list)

    def register(self, topic: typing.Hashable, handler: typing.Callable):
        if not callable(handler):
            raise ValueError('Handler should be a callable object')
        if handler not in self._handler_dict[topic]:
            self._handler_dict[topic].append(handler)

    def unregister(self, topic: typing.Hashable, handler: typing.Callable):
        if handler in self._handler_dict[topic]:
            self._handler_dict[topic].remove(handler)
            if not self._handler_dict[topic]:
                del self._handler_dict[topic]

    def notify(self, topic: typing.Hashable, msg):
        if topic in self._handler_dict:
            for handler in self._handler_dict[topic]:
                handler(msg)


class Subscriber(object):
    
    def __init__(self):
        super(Subscriber, self).__init__()
        self._topic_handler_set = set()
        self._subject: Subject = None 
        
    def subscribe(self, topic: typing.Hashable, handler: typing.Callable):
        self._topic_handler_set.add((topic, handler))
        self._subject.register(topic, handler)

    def unsubscribe(self, topic: typing.Hashable, handler: typing.Callable):
        if (topic, handler) in self._topic_handler_set:
            self._topic_handler_set.remove((topic, handler))
            self._subject.unregister(topic, handler)

    def attach_with(self, subject: Subject):
        self._subject = subject
        self.on_subscribe()

    def detach(self):
        for topic, handler in self._topic_handler_set:
            self._subject.unregister(topic, handler)
        self._topic_handler_set.clear()
        self._subject = None
    
    def on_subscribe(self):
        pass

    def __del__(self):
        self.detach()


class SubjectDecorator(Subject):
    
    def __init__(self):
        super(SubjectDecorator, self).__init__()
        self._subject: Subject = None 
    
    def set_subject(self, subject: Subject):
        self._subject = subject
    
    def notify(self, topic, msg):
        self._subject.notify(topic, msg)
        
    def register(self, topic, handler):
        self._subject.register(topic, handler)
    
    def unregister(self, topic, handler):
        self._subject.unregister(topic, handler)


class Observer(object):
    def update(self):
        pass


class Observable(object):
    def __init__(self):
        super(Observable, self).__init__()
        self._observers: typing.List[Observer] = []

    def notify(self):
        for observer in self._observers:
            observer.update()

    def register(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def unregister(self, observer):
        if observer in self._observers:
            self._observers.remove(observer)


# after 'update' method was called by others, LazyObject can do compute
class LazyObject(Observable, Observer):
    def __init__(self):
        super(LazyObject, self).__init__()
        self._observers = []
        self._calculated = False

    @property
    def calculated(self):
        return self._calculated

    def update(self):
        if self._calculated:
            self._calculated = False
            self.notify()

    def _perform_computations(self):
        pass

    def compute(self):
        if not self._calculated:
            self._perform_computations()
            self._calculated = True


class Registered(object):
    TAG = ''
    subclass_dict = {}

    def __init_subclass__(cls, **kwargs):
        super(Registered, cls).__init_subclass__(**kwargs)
        if Registered in cls.__bases__:
            cls.subclass_dict = {}
        else:
            if cls.TAG in cls.subclass_dict:
                msg = 'Tag "{}" already assigned to {}\n' \
                      'Please consider the risk of overriding'.format(cls.TAG, cls.subclass_dict[cls.TAG])
                warnings.warn(msg)
            cls.subclass_dict[cls.TAG] = cls

    @classmethod
    def factory_create(cls, tag, *args, **kwargs):
        _class = cls.subclass_dict[tag]
        _instance = _class(*args, **kwargs)
        return _instance

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.TAG)


class Engine(object):

    def __init__(self, target=None):
        super(Engine, self).__init__()
        self._thd = Thread()
        self._active = False
        self._target = target

    @property
    def active(self):
        return self._active

    def run(self):
        pass

    def start(self):
        self._active = True
        if not self._thd.isAlive():
            if self._target is not None:
                func = self._target
            else:
                func = self.run
            self._thd = Thread(target=func)
            self._thd.start()
            logger.debug('%s started', self.__class__.__name__)

    def stop(self):
        self._active = False
        if self._thd.isAlive():
            self._thd.join()
            logger.debug('%s stopped', self.__class__.__name__)
