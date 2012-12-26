# -*- coding: utf-8 -*-

import api
from doubanfm import config

class SimpleSourceManager(api.Source):

    def __init__(self, cp):
        self.cp = cp
        sources = config.buildSources(cp)
        if not sources:
            raise Exception, u'没有配置有效的歌曲源'
        self.sources = sources

    def next(self):
        for source in self.sources:
            song = source.next()
            if song:
                return song

    def list(self, size=None):
        result = []
        for source in self.sources:
            temp = source.list(size)
            result.extend(temp)
            if size is not None and len(result) >= size:
                result = result[:size]
                return result

    def skip(self, song):
        song.source.skip(song)

    def select(self, song):
        song.source.select(song)

    def close(self):
        config.saveCookie()
        for source in self.sources:
            source.close()
