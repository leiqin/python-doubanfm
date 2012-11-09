#!/usr/bin/python
# encoding=utf-8

import urllib
import urllib2
import cookielib
import json
import tempfile
import os
import os.path

import cookie

class Douban(object):

    cookiefile = "~/.cache/python-doubanfm/cookies.txt"

    # http://douban.fm/j/mine/playlist?type=e&sid=221320&channel=0&pt=213.4&from=mainsite&r=a2d009faac
    url = 'http://douban.fm/j/mine/playlist'

    def __init__(self):
        self.cookiefile = os.path.expanduser(self.cookiefile)
        cookiejar = cookie.FirecookieCookieJar(self.cookiefile)
        if os.path.exists(self.cookiefile) and os.path.isfile(self.cookiefile):
            cookiejar.load()
        cookieHandler = urllib2.HTTPCookieProcessor(cookiejar)
        self.opener = urllib2.build_opener(cookieHandler)
        self.songs = []
        self.tempfile = None

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
        return self.opener.open(url)

    def _parse(self, response):
        j = json.load(response)
        self.songs = j['song']
        self.songs.reverse()

    def next(self, song = None):
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
            res = self._open(type='s', sid=song.sid, pt=song.time)
            self._parse(res)

        json = self.songs.pop()
        result = Song(json)
        if self.tempfile:
            os.remove(self.tempfile)
        fd, self.tempfile = tempfile.mkstemp()
        r = self.opener.open(result.url)
        data = r.read()
        r.close()
        os.write(fd, data)
        os.close(fd)
        result.file = self.tempfile

        if not self.songs:
            res = self._open(type='p', sid=result.sid, pt=0)
            self._parse(res)
        return result


    def like(self, song):
        res = self._open(type='r', sid=song.sid, pt=song.time)
        self._parse(res)
        song.like = True

    def unlike(self, song):
        res = self._open(type='u', sid=song.sid, pt=song.time)
        self._parse(res)
        song.like = False

class Song(object):

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
        self.time = 0
        self.file = None


if __name__ == '__main__':
    douban = Douban()
    f = douban.opener.open('http://douban.fm/mine?type=played')
    r = f.read()
    print r
