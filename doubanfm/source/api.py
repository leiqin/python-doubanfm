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

    # 歌曲源
    source = None
    # 文件 URI
    uri = None

    # set by Player, Source can read it
    time = 0
    duration = 0

    def info(self):
        raise NotImplementedError

    def oneline(self):
        raise NotImplementedError
