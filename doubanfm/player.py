#!/usr/bin/python
# encoding=utf-8

import threading
import tempfile
import os
import os.path
import urllib2
import pyglet.app
import pyglet.clock
from pyglet.media.avbin import AVbinException

import doubanfm.douban
import doubanfm.util

MAX_LIST_SIZE = 10
MAX_WAIT_TIME = 1024
MIN_WAIT_TIME = 2

class Player(threading.Thread):

    song = None

    def __init__(self):
        pass
        # 由于 pyglet.media 在导入后即便什么也没做
        # 也会在退出时出现警告：
        #
        # AL lib: ReleaseALC: 1 device not closed
        #
        # 虽说好像没什么大问题，但依然很恼人
        # 只有按需导入了
        import pyglet.media

        threading.Thread.__init__(self)
        self.daemon = True

        self.songs = []
        self.condition = threading.Condition()
        self.source = doubanfm.douban.Douban()
        self.player = pyglet.media.Player()
        @self.player.event
        def on_eos():
            if not self.condition.acquire(False):
                return
            try:
                # 更新 self.song.time
                song = self.song
                # duration 和 time 用于判断歌曲是否播放到结束
                # 有时文件头指定的 duration 和歌曲的实际长度并不一致
                # 以实际长度为准
                song.duration = song.time
                waitTime = MIN_WAIT_TIME
                while song == self.song and song.duration == song.time:
                    # 如果是网络故障，当前歌曲没有变
                    # 当前歌曲的播放时间也没变，就继续重试
                    try:
                        self._playnext()
                        break
                    except urllib2.URLError:
                        doubanfm.util.logerror()
                        self.condition.wait(waitTime)
                        if waitTime < MAX_WAIT_TIME:
                            waitTime = waitTime * 2
                        continue
            finally:
                self.condition.release()

        default_update_period = pyglet.media.audio_player_class.UPDATE_PERIOD

        # 常时间播放 CPU 占用率过高的问题找到了
        # 
        # 原方法中有类似如下代码：
        # 
        # underrun = _audio.pump()
        # if underrun:
        #   _audio.UPDATE_PERIOD = _audio.UPDATE_PERIOD * 0.75
        #   _audio.__class__.UPDATE_PERIOD = _audio.__class__.UPDATE_PERIOD * 0.75
        #
        # 意思是如果 _audio 处于播放状态，但是实际的声音引擎处于空闲状态，就是没东西可放
        # 就提高更新频率 ( UPDATE_PERIOD * 0.75 )
        # 但是，只提高不降低，长此以往 CPU 就被占满了
        def dispatch_events(dt=None):
            pyglet.media.Player.dispatch_events(self.player, dt)
            if self.player._audio.UPDATE_PERIOD < default_update_period * 0.5:
                self.player._audio.UPDATE_PERIOD = default_update_period 
            if self.player._audio.__class__.UPDATE_PERIOD < default_update_period * 0.5:
                self.player._audio.__class__UPDATE_PERIOD = default_update_period

        self.player.dispatch_events = dispatch_events

    # 该方法会阻塞
    def run(self):
        try:
            pyglet.app.run()
        except:
            doubanfm.util.logerror()
            raise

    def next(self, index=0):
        with self.condition:
            # 更新 self.song.time
            self.song
            songs = self.songs
            if not index or index < 0 or not songs:
                # 未指定 index，index 无效，未获取列表就使用 index
                self._playnext()
            elif index > len(songs):
                for song in songs:
                    song.source.skip(song)
                self._playnext()
            else:
                while index > 1:
                    song = songs.pop(0)
                    song.source.skip(song)
                    index = index - 1
                song = songs.pop(0)
                song.source.select(song)
                self._playnext(song)
        
    def _next(self, song=None):
        if song:
            if song.mp3source:
                return song
            else:
                try:
                    return self._load(song)
                except AVbinException:
                    doubanfm.util.logerror()

        while True:
            song = self.source.next()
            try:
                return self._load(song)
            except AVbinException:
                doubanfm.util.logerror()

    def _load(self, song):
        tmpfile = song.tmpfile
        song.mp3source = pyglet.media.load(tmpfile or song.file or song.url)
        if tmpfile or song.file:
            song.isLocal = True
        song.duration = song.mp3source.duration
        return song

    def _play(self, song, seek=None):
        with self.condition:
            if self.song and self.song != song:
                self._clearTmpfile()
                self.song.mp3source = None

            self.song = song
            self.songs = []
            self.player.pause()
            self.player.next()
            self.player.queue(song.mp3source)
            if seek:
                self.player.seek(seek)
            self.player.play()
            self.condition.notifyAll()

    def _playnext(self, song=None, seek=None):
        with self.condition:
            song = self._next(song)
            self._play(song, seek)

    def _download(self, song):
        thread = DownloadFile(song)
        thread.start()

    def pause(self):
        with self.condition:
            if not self.player.playing:
                return
            self.player.pause()
            song = self.song
            if not song.isLocal and not song.tmpfile:
                self._download(song)

    def play(self):
        with self.condition:
            if self.player.playing:
                return
            song = self.song
            if song:
                if not song.isLocal and song.tmpfile:
                    song = self._load(song)
                    self._playnext(song, song.time)
                else:
                    self.player.play()
            else:
                self._playnext()

    def list(self):
        with self.condition:
            result = []
            size = MAX_LIST_SIZE
            if self.song:
                result.append(self.song)
                size = size - 1
            self.songs = self.source.list(size)
            if self.songs:
                result.extend(self.songs)
            return result

    def like(self):
        with self.condition:
            song = self.song
            if hasattr(song.source, 'like'):
                m = getattr(song.source, 'like')
                m(song)
                self.songs = []

    def unlike(self):
        with self.condition:
            song = self.song
            if hasattr(song.source, 'unlike'):
                m = getattr(song.source, 'unlike')
                m(song)
                self.songs = []

    def close(self):
        pyglet.app.exit()
        self._clearTmpfile()
        self.source.close()

    def _clearTmpfile(self):
        song = self.song
        if not song:
            return
        tmpfile = song.tmpfile
        if tmpfile and os.path.exists(tmpfile):
            os.remove(tmpfile)
        song.tmpfile = None

    def __getattribute__(self, name):
        if name == 'playing' and self.player:
            return self.player.playing
        elif name == 'time' and self.player:
            return self.player.time
        elif name == 'song' and self.player:
            song = object.__getattribute__(self, name)
            if song:
                song.time = self.time
                return song
            else:
                return None
        else:
            return object.__getattribute__(self, name)

class DownloadFile(threading.Thread):

    def __init__(self, song):
        threading.Thread.__init__(self)
        self.song = song

    def run(self):
        url = self.song.url
        fd, tmpfile = tempfile.mkstemp('.mp3')
        respose = urllib2.urlopen(url)
        while True:
            data = respose.read(4096)
            if not data:
                break
            os.write(fd, data)
        respose.close()
        os.close(fd)
        self.song.tmpfile = tmpfile

# 这一行代码是必需的
# pyglet 是由 pyglet.app.run() 进行实际的播放
# 而该方法最后实际上是一个 select 循环
# 
# while True:
#   select.select(displays,(),(),waitTime)
#   ... ...
#
# displays 是所有的可显示的对象，比如窗口
# 本程序没有那些东西，所以就变成了
# 
# while True:
#   select.select((),(),(),waitTime)
#   ... ...
#
# waitTime 与 clock 有关
# clock 会调度一些需要在未来执行的方法
# waitTime = clock 下一次调度的时间 - 当前时间
#
# 本程序需要调度的方法只是播放，当暂停时，他会被取消调度
# 这样 clock 就没有需要调度的东西了
# 此时：
# waitTime = None
# 
# while True:
#   select.select((),(),(),None)
#   ... ...
#
# 然后，就没有然后了 ...
pyglet.clock.schedule_interval_soft(lambda dt:None, 0.09)


if __name__ == "__main__":
    p = Player()
    p.play()
    p.run()
