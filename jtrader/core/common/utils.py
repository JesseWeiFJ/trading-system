#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import importlib
from collections import OrderedDict


__all__ = [
    'parse_file',
    'format_function',
    'import_class',
]


def parse_file(configs) -> dict:
    if isinstance(configs, dict):
        return configs
    elif configs.endswith('.json'):
        with open(configs, mode='r') as f:
            return json.load(f, object_pairs_hook=OrderedDict)
    else:
        raise ValueError('Can not parse configuration {}'.format(configs))


def format_function(job_func, *args, **kwargs):
    if hasattr(job_func, '__name__'):
        job_func_name = job_func.__name__
        if hasattr(job_func, 'im_class'):
            job_func_name = job_func.im_class.__name__ + '.' + job_func_name
        if hasattr(job_func, '__module__'):
            job_func_name = job_func.__module__ + '.' + job_func_name
    else:
        job_func_name = repr(job_func)
    args = [repr(x) for x in args]
    kwargs = ['%s=%s' % (k, repr(v))
              for k, v in kwargs.items()]
    call_repr = job_func_name + '(' + ', '.join(args + kwargs) + ')'
    return call_repr


def import_class(tag):
    node_path = tag.split('.')
    dir_path = '.'.join(node_path[:-1])
    class_type = node_path[-1]
    module = importlib.import_module(dir_path)
    _class = getattr(module, class_type)
    return _class
