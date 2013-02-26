# -*- coding: utf-8 -*-

import thread
import sys
import pyglet.app
import pyglet.clock
import logging

import api

logger = logging.getLogger(__name__)

class PygletPlayer(api.Player):

    def __init__(self):
        # 由于 pyglet.media 在导入后即便什么也没做
        # 也会在退出时出现警告：
        #
        # AL lib: ReleaseALC: 1 device not closed
        #
        # 虽说好像没什么大问题，但依然很恼人
        # 只有按需导入了
        import pyglet.media

        thread.start_new_thread(pyglet.app.run, ())

        self.player = pyglet.media.Player()
        self.source = None

        @self.player.event
        def on_eos():
            try:
                self.pause()
                self.on_eos()
            except Exception:
                logger.exception(u'on_eos 发生异常')
                raise

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
        default_update_period = pyglet.media.audio_player_class.UPDATE_PERIOD

        def dispatch_events(dt=None):
            pyglet.media.Player.dispatch_events(self.player, dt)
            if self.player._audio.UPDATE_PERIOD < default_update_period * 0.5:
                self.player._audio.UPDATE_PERIOD = default_update_period 
            if self.player._audio.__class__.UPDATE_PERIOD < default_update_period * 0.5:
                self.player._audio.__class__UPDATE_PERIOD = default_update_period

        self.player.dispatch_events = dispatch_events

    def pause(self):
        if not self.player.playing:
            return
        self.player.pause()

    def play(self, uri=None, seek=None):
        if uri:
            self.source = pyglet.media.load(uri)
            self.player.pause()
            self.player.next()
            self.player.queue(self.source)
            self.player.play()
            return
        if seek:
            self.seek(seek)
        if self.player.playing:
            return
        self.player.play()

    def seek(self, seek=None):
        if seek:
            self.player.pause()
            self.player.seek(seek / 1000.0/1000/1000)
            self.player.play()
        return True

    def close(self):
        pyglet.app.exit()

    def __getattribute__(self, name):
        if name == 'playing':
            return self.player.playing
        elif name == 'time': 
            return int(self.player.time * 1000*1000*1000)
        elif name == 'duration':
            if self.source:
                return int(self.source.duration * 1000*1000*1000)
            else:
                return 0
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
    p = PygletPlayer()
    f = sys.argv[1]
    seek = None
    if len(sys.argv) >= 3:
        seek = int(sys.argv[2]) * 1000*1000*1000
    p.play(f, seek)
    print p.duration
    print p.time
    import time
    time.sleep(10)
    
