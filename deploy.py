#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fabric import Connection
from jtrader import __version__
import json
import click

package_name = 'jtrader-' + __version__ + '.tar.gz'


def generate_package(c):
    c.local('python setup.py sdist')


def upload_files(c):
    c.put('dist/' + package_name, '.')
    c.put('requirements.txt', '.')
    print('file uploaded')


def install_package(c):
    with c.prefix('source ~/anaconda3/bin/activate'):
        c.run('pip install ' + package_name)
        c.run('pip install -r requirements.txt')


def delete_files(c):
    c.run('rm ' + package_name)


def deploy(c):
    generate_package(c)
    upload_files(c)
    install_package(c)
    delete_files(c)


@click.command()
# @click.option('--password', prompt=True, hide_input=True,
#               confirmation_prompt=False)
def main():
    with open('host.json') as f:
        fab_config = json.load(f)
        host = fab_config['host']
        user = fab_config['user']
        password = fab_config['password']
    c = Connection(host, user, 22, connect_kwargs={'password': password})
    deploy(c)


if __name__ == '__main__':
    import warnings
    warnings.filterwarnings('ignore')
    main()

