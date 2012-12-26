#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib
import urllib2
import json
import StringIO
import logging

from doubanfm import util
import api

logger = logging.getLogger(__name__)

class Douban(api.Source):

    # http://douban.fm/j/mine/playlist?type=e&sid=221320&channel=0&pt=213.4&from=mainsite&r=a2d009faac
    url = 'http://douban.fm/j/mine/playlist'

    def __init__(self, config):
        self.cookiejar = config.getCookiejar()
        cookieHandler = urllib2.HTTPCookieProcessor(self.cookiejar)
        self.opener = urllib2.build_opener(cookieHandler)
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
                response = self._open(*args, **kargs)
                data = response.read()
                response.close()
                j = json.loads(data)
                songs = map(self._buildSong , j['song'])
                self.songs = songs
                return
            except UnicodeDecodeError:
                # 有时候 json 会有不是 utf-8 的字符
                logger.debug(u'解析歌曲列表 JSON 异常 url = %s', util.decode(response.geturl()))
                logger.debug(response.headers)
                logger.debug(data)
                continue
            except:
                logger.exception(u'解析歌曲列表异常 url = %s', util.decode(response.geturl()))
                logger.error(response.headers)
                logger.error(data)
                raise
            finally:
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
        url = self.url
        if params:
            url = ''.join([url, '?', urllib.urlencode(params)])
        logger.info(u'请求URL %s', util.decode(url))
        response = self.opener.open(url)
        return response

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
        elif size >= len(self.songs):
            return list(self.songs)
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
        pass
        

class Song(api.Song):

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
        self.album = self.data.get('albumtitle')
        self.publicTime = self.data.get('public_time')
        self.picture = self.data.get('picture')
        self.length = self.data.get('length')
        if self.length:
            self.length = float(self.length)

    def info(self):
        output = StringIO.StringIO()
        output.write('Title     : %s\n' % self.title)
        output.write('Artist    : %s\n' % self.artist)
        output.write('Like      : %s\n' % self.like)
        output.write('Album     : %s\n' % self.album)
        if self.publicTime:
            output.write('Public    : %s\n' % self.publicTime)
        output.write(u'Source    : %s\n' % u'豆瓣FM')
        if self.time and self.duration:
            output.write('Time      : %.1f\n' % self.time)
            output.write('Duration  : %.1f\n' % self.duration)
        result = output.getvalue()
        output.close()
        return result

    def oneline(self):
        return ''.join([self.title, ' <', self.artist, '>'])

if __name__ == '__main__':
    douban = Douban()
#    res = douban._open(type='r', sid='35875', pt = 20.0)
#    res.close()
    req = urllib2.Request('http://douban.fm/mine?typed=player')
    f = douban.opener.open(req)
    print req.headers
    print req.unredirected_hdrs
    r = f.read()
    print r
    douban.close()
