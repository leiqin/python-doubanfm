#!/usr/bin/python
# encoding=utf-8

import threading
import pyglet.app
import pyglet.media
import pyglet.clock

import douban

class Player(threading.Thread):

    playing = False
    song = None

    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True

        self.douban = douban.Douban()
        self.player = pyglet.media.Player()
        @self.player.event
        def on_eos():
            if self.song:
                self.song.time = self.song.length
            song = self.douban.next(self.song)
            self.play(song)

    # 该方法会阻塞
    def run(self):
        pyglet.app.run()

    def next(self):
        if self.song:
            self.song.time = self.player.time
        song = self.douban.next(self.song)
        self.play(song)

    def pause(self):
        self.playing = False
        self.player.pause()

    def play(self, song = None):
        self.playing = True
        if not song and self.song:
            self.player.play()
            return
        elif not song:
            song = self.douban.next()

        self.song = song
        self.player.pause()
        self.player.next()
        source = pyglet.media.load(song.url)
        self.player.queue(source)
        self.player.play()

    def like(self):
        self.song.time = self.player.time
        self.douban.like(self.song)

    def unlike(self):
        self.song.time = self.player.time
        self.douban.unlike(self.song)

    def exit(self):
        pyglet.app.exit()

pyglet.clock.schedule_interval_soft(lambda dt:None, 0.05)


if __name__ == "__main__":
    p = Player()
    p.play()
    p.run()
