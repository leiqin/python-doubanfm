# -*- coding: utf-8 -*-

import threading, Queue
import logging

from . import config

logger = logging.getLogger(__name__)

_defaultThreadPool = None

def init():
	global _defaultThreadPool
	if _defaultThreadPool:
		return
	threshold = config.getint('update_threshold', 1)
	_defaultThreadPool = ThreadPool(name='UpdateRSS', threshold=threshold)

def submit(target):
	if not _defaultThreadPool:
		init()
	_defaultThreadPool.submit(target)

def close(target):
	if _defaultThreadPool:
		_defaultThreadPool.close()

class ThreadPool(object):

	def __init__(self, name='default', threshold=1, daemon=True):
		logger.debug(u'初始化线程池 %s' % name)
		self.name = name
		self.threshold = threshold
		self.daemon = daemon
		self.queue = Queue.Queue()
		self.closeFlag = object()
		self.workers = []
		for i in range(self.threshold):
			name = '-'.join([self.name, str(i)])
			logger.debug(u'创建 Worker %s' % name)
			worker = Worker(name, self.queue, self.closeFlag, self.daemon)
			worker.start()
			self.workers.append(worker)

	def submit(self, target):
		self.queue.put(target)

	def close(self):
		logger.debug(u'关闭线程池 %s' % self.name)
		for i in range(self.threshold):
			self.queue.put(self.closeFlag)

class Worker(threading.Thread):

	def __init__(self, name, queue, closeFlag, daemon=True):
		threading.Thread.__init__(self)
		self.name = name
		self.daemon = daemon
		self.queue = queue
		self.closeFlag = closeFlag

	def run(self):
		while True:
			target = self.queue.get()
			if target is self.closeFlag:
				logger.debug(u'退出 Worker %s' % self.name)
				return
			try:
				logger.debug(u'%s 运行 target %s' % (self.name, repr(target)))
				target()
			except Exception:
				logger.error(u'线程池 %s 发生异常' % self.name)

