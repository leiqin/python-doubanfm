#!/usr/bin/python
# encoding=utf-8

import urllib
import urllib2
import cookielib
import json
import os
import os.path
import StringIO

import lqfm.cookie
import lqfm.util

class Douban(object):

    # http://douban.fm/j/mine/playlist?type=e&sid=221320&channel=0&pt=213.4&from=mainsite&r=a2d009faac
    url = 'http://douban.fm/j/mine/playlist'

    def __init__(self):
        self.cookiefile = lqfm.util.expand(lqfm.util.cookiefile)
        policy = lqfm.cookie.MyCookiePolicy()
        self.cookiejar = lqfm.cookie.FirecookieCookieJar(self.cookiefile, policy=policy)
        if os.path.exists(self.cookiefile) and os.path.isfile(self.cookiefile):
            # ignore_expires=True 表示加载过期的 cookie
            self.cookiejar.load(ignore_discard=True, ignore_expires=True)
        cookieHandler = urllib2.HTTPCookieProcessor(self.cookiejar)
        self.opener = urllib2.build_opener(cookieHandler)
        self.song = None
        self.songs = []

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
        f = self.opener.open(url)
        return f

    def _parse(self, response):
        j = json.load(response)
        songs = map(self._buildSong , j['song'])
        self.songs = songs
    
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
            res = self._open(type='e', sid=self.song.sid, pt=self.song.time)
            res.close()
        else:
            # hand
            res = self._open(type='s', sid=self.song.sid, pt=self.song.time)
            self._parse(res)

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
            res = self._open(type='e', sid=self.song.sid, pt=self.song.time)
            res.close()
        else:
            # hand
            res = self._open(type='s', sid=self.song.sid, pt=self.song.time)
            # 不更新列表
            res.close()

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
                res = self._open(type='p', sid=self.song.sid, pt=0)
                self._parse(res)
            else:
                res = self._open()
                self._parse(res)

    def like(self, song):
        res = self._open(type='r', sid=song.sid, pt=song.time)
        self._parse(res)
        song.like = True

    def unlike(self, song):
        res = self._open(type='u', sid=song.sid, pt=song.time)
        self._parse(res)
        song.like = False

    def close(self):
        self.cookiejar.save(ignore_discard=True, ignore_expires=True)
        

class Song(object):

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
        output.write('Public    : %s\n' % self.publicTime)
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
