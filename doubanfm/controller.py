#!/usr/bin/python
# -*- coding: utf-8 -*-

import threading
import sys
import urllib2
import logging

import player.gstearmer

logger = logging.getLogger(__name__)

MAX_LIST_SIZE = 10
MAX_WAIT_TIME = 1024
MIN_WAIT_TIME = 2

class Controller(object):

    _song = None

    @property
    def song(self):
        if not self._song:
            return None
        self._song.time = self.time
        return self._song

    def __init__(self, source=None):
        self.songs = []
        self._song = None
        self.condition = threading.Condition()
        self.source = source
        self.player = player.gstearmer.GstPlayer()
        def on_eos():
            if not self.condition.acquire(False):
                return
            try:
                # 更新 self._song.time
                # duration 和 time 用于判断歌曲是否播放到结束
                # 有时文件头指定的 duration 和歌曲的实际长度并不一致
                # 以实际长度为准
                if self._song:
                    self._song.time = self.time
                    self._song.duration = self._song.time
                if not self.source:
                    self.pause()
                    return
                self.next()
            finally:
                self.condition.release()
        self.player.on_eos = on_eos
        self.player.on_err = on_eos

    def nextSong(self):
        with self.condition:
            waitTime = MIN_WAIT_TIME
            while True:
                # 如果是网络故障，就继续重试
                try:
                    return self.source.next()
                except urllib2.URLError:
                    logger.warning('获取下一首歌曲时，网络访问异常', exc_info=sys.exc_info())
                    self.condition.wait(waitTime)
                    if waitTime < MAX_WAIT_TIME:
                        waitTime = waitTime * 2
                    continue


    def next(self, index=0):
        with self.condition:
            songs = self.songs
            song = None
            if not index or index < 0 or not songs:
                # 未指定 index，index 无效，未获取列表就使用 index
                song = self.nextSong()
            elif index > len(songs):
                for song in songs:
                    self.source.skip(song)
                song = self.nextSong()
            else:
                while index > 1:
                    song = songs.pop(0)
                    self.source.skip(song)
                    index = index - 1
                song = songs.pop(0)
                self.source.select(song)
            self.playSong(song)
        
    def pause(self):
        with self.condition:
            if not self.player.playing:
                return
            self.player.pause()

    def play(self, song=None, seek=None):
        with self.condition:
            if song:
                self.playSong(song, seek)
                return
            if not self._song:
                self.next()
                return
            if self.player.playing:
                return
            self.player.play()

    def playSong(self, song, seek=None):
        # 更新 self._song.time
        if self._song:
            self._song.time = self.time
        self._song = song
        if not self._song:
            self.pause()
            return
        self.player.play(self._song.uri, seek)
        self._song.duration = self.player.duration

    def list(self):
        with self.condition:
            result = []
            size = MAX_LIST_SIZE
            if self._song:
                result.append(self.song)
                size = size - 1
            self.songs = self.source.list(size)
            if self.songs:
                result.extend(self.songs)
            return result

    def like(self):
        with self.condition:
            song = self._song
            if song and hasattr(song.source, 'like'):
                m = getattr(song.source, 'like')
                m(song)
                self.songs = []

    def unlike(self):
        with self.condition:
            song = self._song
            if song and hasattr(song.source, 'unlike'):
                m = getattr(song.source, 'unlike')
                m(song)
                self.songs = []

    def close(self):
        self.player.close()
        self.source.close()

    def update(self):
        if hasattr(self.source, 'update'):
            self.source.update()

    def channel(self, name):
        with self.condition:
            if hasattr(self.source, 'channel'):
                m = getattr(self.source, 'channel')
                if m(name):
                    self.songs = []
                    self._song = None
                    if self.playing:
                        self.next()

    def listChannel(self):
        with self.condition:
            if hasattr(self.source, 'listChannel'):
                m = getattr(self.source, 'listChannel')
                return m()

    def __getattribute__(self, name):
        if name == 'playing':
            return self.player.playing
        elif name == 'time':
            return self.player.time
        else:
            return object.__getattribute__(self, name)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    import source.api
    class Song(source.api.Song):

        def __init__(self, file):
            self.file = file

        def info(self):
            return self.file

        def oneline(self):
            return self.file
    p = Controller()
    f = sys.argv[1]
    seek = None
    if len(sys.argv) >= 3:
        seek = int(sys.argv[2])
    p.play(Song(f), seek)
    p.run()
