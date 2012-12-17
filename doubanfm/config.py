#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path, logging.config
import ConfigParser
import logging
import threading
import time

import util, cookie

logger = logging.getLogger(__name__)

configdir = os.path.expanduser(util.configdir)
cachedir = os.path.expanduser(util.cachedir)
logconf = os.path.join(configdir, 'logging.conf')
conf = os.path.join(configdir, 'doubanfm.conf')

def init():
    util.initDir(configdir)
    util.initDir(cachedir)

    if not os.path.exists(logconf):
        d = os.path.dirname(__file__)
        default_logconf = os.path.join(d, 'logging.default.conf')
        copyfile(default_logconf, logconf)

    if not os.path.exists(conf):
        d = os.path.dirname(__file__)
        default_conf = os.path.join(d, 'doubanfm.default.conf')
        copyfile(default_conf, conf)

def copyfile(src, dest):
    with open(src) as s:
        with open(dest, 'w') as d:
            data = s.read()
            d.write(data)

def load():
    default = {
            'home' : os.path.expanduser('~'),
            'configdir' : configdir,
            'cachedir' : cachedir,
            }
    logging.config.fileConfig(logconf, default, False)

    cp = ConfigParser.ConfigParser(default)
    cp.read(conf)
    return cp

cookiejars = {}

def close():
    saveCookie()

def saveCookie():
    logger.debug(u'保存 Cookie')
    for cookiejar in cookiejars.values():
        cookiejar.save(ignore_discard=True, ignore_expires=True)

def buildSources(cp):
    result = []
    for name in cp.sections():
        if name in ['common', 'global']:
            continue
        if not cp.has_option(name, 'class'):
            logger.warning(u'无效的歌曲源 %s ，没有配置 class', name)
            continue
        cla = cp.get(name, 'class')
        logger.debug(u'创建歌曲源 %s ，class = %s', name, cla)
        cla = _resolve(cla)
        config = Config(cp, name)
        source = cla(config)
        result.append(source)
    return result

def _resolve(name):
    """Resolve a dotted name to a global object."""
    # copy from logging.config
    name = name.split('.')
    used = name.pop(0)
    found = __import__(used)
    for n in name:
        used = used + '.' + n
        try:
            found = getattr(found, n)
        except AttributeError:
            __import__(used)
            found = getattr(found, n)
    return found

class Config(object):

    def __init__(self, cp, name):
        self.cp = cp
        self.name = name

    def __getitem__(self, key):
        value = self.get(key)
        if value is None:
            return value
        else:
            raise KeyError, key

    def get(self, key):
        if self.cp.has_option(self.name, key):
            return self.cp.get(self.name, key)
        if self.cp.has_option('common', key):
            return self.cp.get('common', key)
        return None

    def getCookiejar(self):
        cookiefile = self.get('cookiefile')
        if cookiefile in cookiejars:
            return cookiejars[cookiefile]
        policy = cookie.MyCookiePolicy()
        cookiejar = cookie.FirecookieCookieJar(cookiefile, policy=policy)
        cookiejars[cookiefile] = cookiejar
        if os.path.exists(cookiefile) and os.path.isfile(cookiefile):
            # ignore_expires=True 表示加载过期的 cookie
            cookiejar.load(ignore_discard=True, ignore_expires=True)
        return cookiejar

class SaveCookie(threading.Thread):

    def __init__(self, interval=3600):
        threading.Thread.__init__(self)
        self.daemon = True
        
        self.interval = interval

    def run(self):
        while True:
            time.sleep(self.interval)
            saveCookie()
