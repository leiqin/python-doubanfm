# -*- coding: utf-8 -*-

import logging, itertools

import api
from doubanfm import config

logger = logging.getLogger(__name__)

class SimpleSourceManager(api.Source):
    '''
    注意： 该类是线程不安全的
    '''

    def __init__(self, cp):
        self.cp = cp
        sources = config.buildSources(cp)
        if not sources:
            raise Exception, u'没有配置有效的歌曲源'
        self.sources = itertools.cycle(sources)
        self.source = self.sources.next()
        self.count = 0
        self.threshold = self.source.conf.getint('threshold', 1)

    def next(self):
        source = self.source
        while True:
            song = self._nextSong()
            if song:
                return song
            self._nextSource()
            if source is self.source:
                return None

    def _nextSong(self):
        song = self.source.next()
        if song:
            self.count += 1
        if self.threshold >= 0 and self.count >= self.threshold:
            self._nextSource()
        return song

    def _nextSource(self):
        self.source = self.sources.next()
        self.count = 0
        self.threshold = self.source.conf.getint('threshold', 1)

    def list(self, size=None):
        result = []
        source = self.source
        while True:
            temp = source.list(size)
            result.extend(temp)
            if size is not None and len(result) >= size:
                result = result[:size]
                break
            source = self.sources.next()
            if source is self.source:
                break
        while source is not self.source:
            source = self.sources.next()
        return result

    def skip(self, song):
        song.source.skip(song)

    def select(self, song):
        song.source.select(song)

    def update(self):
        for source in self.sources:
            if hasattr(source, 'update'):
                source.update()

    def close(self):
        config.saveCookie()
        for source in self.sources:
            source.close()
