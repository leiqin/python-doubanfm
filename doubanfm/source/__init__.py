# -*- coding: utf-8 -*-

import logging, itertools, collections

from .api import Source, Song
from .. import config

logger = logging.getLogger(__name__)

class SimpleSourceManager(Source):
	'''
	注意： 该类是线程不安全的
	'''

	def __init__(self, sources=None):
		if not sources:
			sources = []
		self.rawSources = sources
		self.sources = itertools.cycle(self.rawSources)
		self.source = None
		self.count = 0
		self.threshold = 0

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
		if not self.source:
			self._nextSource()
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
		for source in self.rawSources:
			if hasattr(source, 'update'):
				source.update()

	def close(self):
		config.saveCookie()
		for source in self.rawSources:
			source.close()

class SimpleChannelSourceManager(Source):

	def __init__(self, sources):
		self.rawSources = sources
		self.channels = collections.defaultdict(SimpleSourceManager)
		self.current = self.channels[config.get('default_channel', 'all')]
		for source in self.rawSources:
			self.channels['all'].addSource(source)
			for c in source.conf.get('channel', '').split(','):
				if not c or c == 'all':
					continue
				self.channels[c].addSource(source)

	def listChannel(self):
		result = []
		for name, channel in self.channels.items():
			if channel is self.current:
				result.append('* %s' % name)
			else:
				result.append('  %s' % name)
		return '\n'.join(result)

	def channel(self, name):
		if name in self.channels:
			if self.current is self.channels[name]:
				return False
			else:
				self.current = self.channels[name]
				return True
		else:
			raise Exception, 'no channel %s' % name

	def update(self):
		for source in self.rawSources:
			if hasattr(source, 'update'):
				source.update()

	def close(self):
		config.saveCookie()
		for source in self.rawSources:
			source.close()

	def next(self):
		return self.current.next()

	def list(self, size=None):
		return self.current.list(size)

	def skip(self, song):
		return self.current.skip(song)

	def select(self, song):
		return self.current.select(song)
