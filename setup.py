#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Jtrader, real-time trading framework for spot, futures and swaps asset in stock and crypto-currency market
"""


from setuptools import setup, find_packages
import jtrader


def extract_packages(package):
    packages = find_packages(package)
    packages = list(map(lambda x: package + '.' + x, packages))
    packages.append(package)
    return packages


setup(
    name='jtrader',
    version=jtrader.__version__,
    author=jtrader.__author__,
    description='Quantitative Trading System',
    long_description=__doc__,
    keywords=['trading', 'development'],
    author_email='jesseweifj@gmail.com',
    packages=extract_packages('jtrader'),
    # packages=['jtrader'],
    include_package_data=True,
    install_requires=[],
)
