#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path, logging.config

import util

configdir = os.path.expanduser(util.configdir)
cachedir = os.path.expanduser(util.cachedir)
logconf = os.path.join(configdir, 'logging.conf')

def init():
    util.initDir(configdir)
    util.initDir(cachedir)

    if os.path.exists(logconf):
        return
    util.initParent(logconf)
    d = os.path.dirname(__file__)
    defaultconf = os.path.join(d, 'logging.default.conf')
    with open(defaultconf) as dc:
        with open(logconf, 'w') as lc:
            data = dc.read()
            lc.write(data)

def load():
    default = {
            'home' : os.path.expanduser('~'),
            'configdir' : configdir,
            'cachedir' : cachedir,
            }
    logging.config.fileConfig(logconf, default, False)

