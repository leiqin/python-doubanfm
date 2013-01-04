#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path, logging.config
import ConfigParser
import logging
import threading
import time

import util, cookie

logger = logging.getLogger(__name__)

TIMEOUT = 30

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
        cla = util.resolve(cla)
        config = Config(name, cp)
        source = cla(config)
        result.append(source)
    return result

class Config(object):

    def __init__(self, name, cp=None):
        self.name = name
        if cp is None:
            cp = ConfigParser.ConfigParser()
            cp.add_section('common')
            cp.add_section(name)
        self.cp = cp

    def __contains__(self, key):
        return self.cp.has_option(self.name, key) or \
                self.cp.has_option('common', key)

    def __getitem__(self, key):
        value = self.get(key)
        if value is None:
            return value
        else:
            raise KeyError, key

    def __setitem__(self, key, value):
        self.set(key, value)

    def getint(self, key):
        if self.cp.has_option(self.name, key):
            return self.cp.getint(self.name, key)
        if self.cp.has_option('common', key):
            return self.cp.getint('common', key)
        return None

    def getfloat(self, key):
        if self.cp.has_option(self.name, key):
            return self.cp.getfloat(self.name, key)
        if self.cp.has_option('common', key):
            return self.cp.getfloat('common', key)
        return None

    def getboolean(self, key):
        if self.cp.has_option(self.name, key):
            return self.cp.getboolean(self.name, key)
        if self.cp.has_option('common', key):
            return self.cp.getboolean('common', key)
        return None

    def get(self, key):
        if self.cp.has_option(self.name, key):
            return self.cp.get(self.name, key)
        if self.cp.has_option('common', key):
            return self.cp.get('common', key)
        return None

    def set(self, key, value):
        if value is not None or type(value) != str or type(value) != unicode:
            value = str(value)
        self.cp.set(self.name, key, value)

    def getName(self):
        if 'name' in self:
            return util.decode(self.get('name'))
        else:
            return self.name

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
