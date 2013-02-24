# -*- coding: utf-8 -*-

import logging, itertools

import api
from doubanfm import config

logger = logging.getLogger(__name__)

class SimpleSourceManager(api.Source):
    '''
    注意： 该类是线程不安全的
    '''

    def __init__(self, sources=None):
        if not sources:
            sources = []
        self.rawSources = sources
        self.sources = itertools.cycle(self.rawSources)

    def addSource(self, source):
        self.rawSources.append(source)
        self.sources = itertools.cycle(self.rawSources)

    def next(self):
        if not self.rawSources:
            return None
        if not self.source:
            self._nextSource()
        source = self.source
        while True:
            song = self._nextSong()
            if song:
                return song
            self._nextSource()
            if source is self.source:
                return self._nextSong()

    def _nextSong(self):
        if self.threshold > 0 and self.count >= self.threshold:
            return None
        song = self.source.next()
        if song:
            self.count += 1
            logger.debug(song.oneline())
        logger.debug(song)
        return song

    def _nextSource(self):
        self.source = self.sources.next()
        self.count = 0
        self.threshold = self.source.conf.getint('threshold', 0)
        logger.debug(u'选择源 %s' % self.source.name)

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
        for source in self.rawSources:
            source.close()
