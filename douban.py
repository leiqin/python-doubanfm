#!/usr/bin/python
# encoding=utf-8

import glob

g = glob.iglob("/home/leiqin/Music/*.mp3")
            
class Douban(object):

    cookiefile = "~/.cache/python-doubanfm/cookie.txt"

    def __init__(self):
        pass

    def next(self, song = None):
        if song:
            print song.time
        else:
            song = Song()
        song.url = g.next()
        print song.url
        return song


    def like(self, song):
        pass

    def unlike(self, song):
        pass
        

class Song(object):

    def __init__(self, data = {}):
        self.data = data
        self.sid = self.data.get('sid')
        self.title = self.data.get('title')
        self.like = self.data.get('like')
        self.artist = self.data.get('artist')
        self.url = self.data.get('url')
        self.album = self.data.get('albumtitle')
        self.publicTime = self.data.get('public_time')
        self.picture = self.data.get('picture')
        self.length = self.data.get('length')
        self.time = 0

