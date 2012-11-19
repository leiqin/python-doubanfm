#!/usr/bin/python
# encoding=utf-8

import threading
import pyglet.app
import pyglet.clock
from pyglet.media.avbin import AVbinException

import douban
import util

MAX_LIST_SIZE = 10

class Player(threading.Thread):

    playing = False
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
        self.lock = threading.Lock()
        self.source = douban.Douban()
        self.player = pyglet.media.Player()
        @self.player.event
        def on_eos():
            # 更新 self.song.time
            song = self.song
            if song:
                # duration 和 time 用于判断歌曲是否播放到结束
                # 有时文件头指定的 duration 和歌曲的实际长度并不一致
                song.duration = song.time
            self._playnext(blocking=False)

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
            util.logerror()

    def next(self, index=0):
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
                    util.logerror()

        while True:
            song = self.source.next()
            try:
                return self._load(song)
            except AVbinException:
                util.logerror()

    def _load(self, song):
        song.mp3source = pyglet.media.load(song.file or song.url)
        song.duration = song.mp3source.duration
        return song

    def _play(self, song):
        self.playing = True
        self.song = song
        self.songs = []
        self.player.pause()
        self.player.next()
        self.player.queue(song.mp3source)
        self.player.play()

    def _playnext(self, song=None, blocking=True):
        if not self.lock.acquire(blocking):
            return
        try:
            song = self._next(song)
            self._play(song)
        finally:
            self.lock.release()

    def pause(self):
        self.playing = False
        self.player.pause()

    def play(self, song = None):
        self.playing = True
        if not song and self.song:
            self.player.play()
            return
        self._playnext(song)


    def list(self):
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
        song = self.song
        if hasattr(song.source, 'like'):
            m = getattr(song.source, 'like')
            m(song)

    def unlike(self):
        song = self.song
        if hasattr(song.source, 'unlike'):
            m = getattr(song.source, 'unlike')
            m(song)

    def close(self):
        pyglet.app.exit()
        self.source.close()

    def __getattribute__(self, name):
        if name == 'time' and self.player:
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
