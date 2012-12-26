# -*- coding: utf-8 -*-

class Source(object):

    def next(self):
        raise NotImplementedError

    def list(self, size=None):
        return []

    def skip(self, song):
        pass

    def select(self, song):
        pass

    def close(self):
        pass

class Song(object):

    source = None
    # local file
    file = None
    # network file
    url = None

    # set by Player, Source can read it
    time = 0
    duration = 0

    # used by Player, please don't use it in Source
    isLocal = False
    tmpfile = None
    mp3source = None

    def info(self):
        raise NotImplementedError

    def oneline(self):
        raise NotImplementedError
