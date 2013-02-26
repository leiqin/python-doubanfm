# -*- coding:utf-8 -*-

import os, os.path, random
import logging

import api
from doubanfm import util

logger = logging.getLogger(__name__)

class Random(api.Source):
    '''
    本地随机源

    配置参数：
        path (必须) <string> 本地音乐文件的目录，多个目录用冒号 : 分割
        suffix (可选) <string> 音乐文件的后缀，如有多个用逗号 , 分割，默认为 .mp3
        threshold (可选) <int> 当有多个源时，每次该源播放的歌曲数，0 表示放完为止，默认为 1
    '''

    def __init__(self, conf):
        self.conf = conf
        self.name = u'本地随机'
        self.paths = [x for x in self.conf.get('path').split(':') if x]
        self.suffix = tuple(x for x in self.conf.get('suffix', '.mp3') if x)
        self.songs = []
        for path in self.paths:
            for top, dirs, files in os.walk(path):
                for filename in files:
                    if filename.endswith(self.suffix):
                        fullpath = os.path.join(top, filename)
                        song = Song(fullpath)
                        song.source = self
                        self.songs.append(song)


    def next(self):
        if not self.songs:
            return None
        return self.songs[random.randint(0, len(self.songs)-1)]


class Song(api.Song):

    def __init__(self, path):
        self.uri = path
        filename = os.path.basename(path)
        index = filename.rfind('.')
        if index != -1:
            self.name = filename[:index]
        else:
            self.name = filename
        self.name = util.decode(self.name)

    def info(self):
        result = []
        result.append(u'Title     : %s' % self.name)
        if self.source:
            result.append(u'Source    : %s' % self.source.name)
        if self.time and self.duration:
            result.append(u'Time      : %s' % util.showtime(self.time))
            result.append(u'Duration  : %s' % util.showtime(self.duration))
        return '\n'.join(result)

    def oneline(self):
        return util.decode(self.name)
