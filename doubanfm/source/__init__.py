# -*- coding: utf-8 -*-

import api

class SimpleSourceManager(api.Source):

    def __init__(self, sources):
        if sources:
            if isinstance(sources, api.Source):
                self.sources = [sources]
            else:
                self.sources = sources
        else:
            self.sources = []

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
        for source in self.sources:
            source.close()
