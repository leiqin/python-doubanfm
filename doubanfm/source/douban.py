#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib, urllib2, json, StringIO, random, string
import logging

from .. import util, config
from .api import Source, Song

logger = logging.getLogger(__name__)

class Douban(Source):
    '''
    豆瓣FM

    配置参数：
        cookiefile (可选) <string> cookie 文件路径，格式为 FireCookie(Firefox 插件) 导出格式
        threshold (可选) <int> 当有多个源时，每次该源播放的歌曲数，0 表示放完为止，默认为 1
    '''

    # http://douban.fm/j/mine/playlist?type=e&sid=221320&channel=0&pt=213.4&from=mainsite&r=a2d009faac
    url = 'http://douban.fm/j/mine/playlist'

    def __init__(self, conf=None):
        self.conf = conf
        self.opener = urllib2.build_opener()
        self.name = u'豆瓣FM'

        if conf and 'cookiefile' in self.conf:
            self.cookiejar = self.conf.getCookiejar()
            cookieHandler = urllib2.HTTPCookieProcessor(self.cookiejar)
            self.opener.add_handler(cookieHandler)
        self.song = None
        self.songs = []

    def notifyDouban(self, *args, **kargs):
        '''通知豆瓣FM，不处理结果，参数同 _open()'''
        response = self._open(*args, **kargs)
        response.close()

    def updateSongs(self, *args, **kargs):
        '''通知豆瓣FM，处理结果，更新歌曲列表，参数同 _open()'''
        while True:
            try:
                response = None
                response = self._open(*args, **kargs)
                data = response.read()
                response.close()
                j = json.loads(data)
                songs = map(self._buildSong , j['song'])
                self.songs = songs
                return
            except UnicodeDecodeError:
                # 有时候 json 会有不是 utf-8 的字符
                if response:
                    logger.debug(u'解析歌曲列表 JSON 异常 url = %s', util.decode(response.geturl()))
                    logger.debug(response.headers)
                    logger.debug(data)
                else:
                    logger.debug('response is None')
                continue
            except Exception:
                if response:
                    logger.exception(u'解析歌曲列表异常 url = %s', util.decode(response.geturl()))
                    logger.error(response.headers)
                    logger.error(data)
                else:
                    logger.debug('response is None')
                raise
            finally:
                if response:
                    response.close()
            

    def _open(self, type='n', sid=None, channel=0, pt=None):
        params = {}
        if type:
            params['type'] = type
        if sid:
            params['sid'] = sid
        if channel != None:
            params['channel'] = channel
        if pt != None:
            params['pt'] = '%.1f' % pt
        params['from'] = 'mainsite'
        params['r'] = self.random()
        url = self.url
        if params:
            url = ''.join([url, '?', urllib.urlencode(params)])
        logger.info(u'请求URL %s', util.decode(url))
        response = self.opener.open(url, timeout=config.getint('timeout', 30))
        return response

    randomString = '0123456789' + string.ascii_lowercase

    def random(self):
        result = []
        b = len(self.randomString) - 1
        for i in range(10):
            result.append(self.randomString[random.randint(0, b)])
        return ''.join(result)

    def _buildSong(self, data):
        song = Song(data)
        song.source = self
        return song

    def next(self):
        if not self.song:
            # new
            pass
        elif self.song.time >= self.song.duration:
            # reach end
            self.notifyDouban(type='e', sid=self.song.sid, pt=self.song.time)
        else:
            # hand
            self.updateSongs(type='s', sid=self.song.sid, pt=self.song.time)

        self._checksongs()
        self.song = self.songs.pop(0)
        self._checksongs()

        return self.song

    def skip(self, song):
        try:
            self.songs.remove(song)
        except ValueError:
            pass

    def select(self, song):
        if not self.song:
            # new
            pass
        elif self.song.time >= self.song.duration:
            # reach end
            self.notifyDouban(type='e', sid=self.song.sid, pt=self.song.time)
        else:
            # hand
            # 不更新列表
            self.notifyDouban(type='s', sid=self.song.sid, pt=self.song.time)

        self.song = song
        self.skip(song)
        self._checksongs()

    def list(self, size=None):
        if size is None:
            return list(self.songs)
        elif size <= 0:
            return []
        else:
            return self.songs[:size]
            

    def _checksongs(self):
        if not self.songs:
            if self.song:
                self.updateSongs(type='p', sid=self.song.sid, pt=0)
            else:
                self.updateSongs()

    def like(self, song):
        if song.like:
            return
        self.updateSongs(type='r', sid=song.sid, pt=song.time)
        song.like = True

    def unlike(self, song):
        if not song.like:
            return
        self.updateSongs(type='u', sid=song.sid, pt=song.time)
        song.like = False

    def close(self):
        self.opener.close()
        

class Song(Song):

    source = None
    time = 0
    duration = 0
    url = None
    file = None

    isLocal = False
    tmpfile = None
    mp3source = None

    def __init__(self, data = {}):
        self.data = data
        self.sid = self.data.get('sid')
        self.title = self.data.get('title')
        self.like = self.data.get('like')
        if self.like:
            self.like = True
        else:
            self.like = False
        self.artist = self.data.get('artist')
        self.url = self.data.get('url')
        self.uri = self.url
        self.album = self.data.get('albumtitle')
        self.publicTime = self.data.get('public_time')
        self.picture = self.data.get('picture')
        self.length = self.data.get('length')
        if self.length:
            self.length = float(self.length)

    def info(self):
        result = []
        result.append('Title     : %s' % self.title)
        result.append('Artist    : %s' % self.artist)
        result.append('Like      : %s' % self.like)
        result.append('Album     : %s' % self.album)
        if self.publicTime:
            result.append('Public    : %s' % self.publicTime)
        if self.source:
            result.append(u'Source    : %s' % self.source.name)
        if self.time and self.duration:
            result.append('Time      : %s' % util.showtime(self.time))
            result.append('Duration  : %s' % util.showtime(self.duration))
        return '\n'.join(result)

    def oneline(self):
        return ''.join([self.title, ' <', self.artist, '>'])

if __name__ == '__main__':
    import sys
    logging.basicConfig(level=logging.DEBUG)
    conf = config.Config()
    conf['cookiefile'] = '/home/leiqin/.cache/python-doubanfm/cookies.txt'
    douban = Douban(conf)
    if len(sys.argv) >= 2 and sys.argv[1] == 'liked':
        req = urllib2.Request('http://douban.fm/mine?typed=liked')
        f = douban.opener.open(req)
        print req.headers
        print req.unredirected_hdrs
        r = f.read()
        print r
        douban.close()
    else:
        for i in range(5):
            song = douban.next()
            print song.info()
            print song.url
            print ''
