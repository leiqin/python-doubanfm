#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path, logging.config

import util

logconf = os.path.expanduser('~/.config/python-doubanfm/logging.conf')

def init():
    util.initDir(os.path.expanduser('~/.cache/python-doubanfm'))
    if os.path.exists(logconf):
        return
    util.initParent(logconf)
    d = os.path.dirname(__file__)
    defaultconf = os.path.join(d, 'logging.default.conf')
    with open(defaultconf) as dc:
        with open(logconf, 'w') as lc:
            data = dc.read()
            home = os.path.expanduser('~')
            data = data.replace('~', home)
            lc.write(data)

def load():
    logging.config.fileConfig(logconf,disable_existing_loggers=False)

