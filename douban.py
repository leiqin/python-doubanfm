#!/usr/bin/python
# encoding=utf-8

import urllib
import urllib2
import cookielib
import json
import os
import os.path
import threading
import StringIO

import cookie
import util

class Douban(object):

    # http://douban.fm/j/mine/playlist?type=e&sid=221320&channel=0&pt=213.4&from=mainsite&r=a2d009faac
    url = 'http://douban.fm/j/mine/playlist'

    def __init__(self):
        self.cookiefile = util.expand(util.cookiefile)
        policy = cookie.MyCookiePolicy()
        self.cookiejar = cookie.FirecookieCookieJar(self.cookiefile, policy=policy)
        if os.path.exists(self.cookiefile) and os.path.isfile(self.cookiefile):
            # ignore_expires=True 表示加载过期的 cookie
            self.cookiejar.load(ignore_discard=True, ignore_expires=True)
        cookieHandler = urllib2.HTTPCookieProcessor(self.cookiejar)
        self.opener = urllib2.build_opener(cookieHandler)
        self.songs = []
        self.lock = threading.Lock()

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
        songs = map(Song , j['song'])
        self.songs = songs

    def next(self, song=None, blocking=True, index=0):
        if not self.lock.acquire(blocking):
            return
        try:
            if not song:
                # new
                if not self.songs:
                    res = self._open()
                    self._parse(res)
            elif song.time >= song.length:
                # reach end
                res = self._open(type='e', sid=song.sid, pt=song.time)
                res.close()
                if not self.songs:
                    res = self._open(type='p', sid=song.sid, pt=0)
                    self._parse(res)
            else:
                # hand
                if index <=0 or index > len(self.songs):
                    res = self._open(type='s', sid=song.sid, pt=song.time)
                    self._parse(res)
                else:
                    while index > 1:
                        self.songs.pop(0)
                        index = index - 1

            result = self.songs.pop(0)

            if not self.songs:
                res = self._open(type='p', sid=result.sid, pt=0)
                self._parse(res)

            return result
        finally:
            self.lock.release()

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

    time = 0
    duration = 0
    file = None
    url = None
    tmpfile = None

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
            output.write('Time      : %.2f\n' % self.time)
            output.write('Duration  : %.2f\n' % self.duration)
        result = output.getvalue()
        output.close()
        return result

    def oneline(self):
        return ''.join(self.title, ' <', self.artist, '>')


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
