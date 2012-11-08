#!/usr/bin/python
# encoding=utf-8

import os
import os.path

import player
import util


pipefile = os.path.expanduser("~/.cache/pythen-doubanfm/pipe")

def start():
    p = player.Player()
    p.play()
    p.start()

    mkpipe(pipefile)

    f = open(pipefile, 'r')
    while True:
        cmd = f.read(1)
        if not cmd:
            f.close()
            f = open(pipefile, 'r')
        elif cmd == 'n':
            p.next()
        elif cmd == 'p':
            if not p.playing:
                p.play()
        elif cmd == 'P':
            if p.playing:
                p.pause()
        elif cmd == 'G':
            if p.playing:
                p.pause()
            else:
                p.play()
        elif cmd == 'l':
            if not p.song.like:
                p.like()
        elif cmd == 'u':
            if p.song.like:
                p.unlike()
        elif cmd == 'L':
            if p.song.like:
                p.unlike()
            else:
                p.like()
        elif cmd == 'x':
            p.exit()
            os.remove(pipefile)
            return

def mkpipe(pipefile):
    util.initParent(pipefile)
    if os.path.exists(pipefile):
        os.remove(pipefile)
    os.mkfifo(pipefile, 0600)
        

if __name__ == "__main__":
    start()
