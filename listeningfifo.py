#!/usr/bin/python
# encoding=utf-8

import threading
import os
import os.path

import player
import util

class Listening(threading.Thread):

    pipefile = "~/.cache/pythen-doubanfm/pipe"

    def run(self):
        p = player.Player()
        p.play()
        p.start()

        pipefile = os.path.expanduser(self.pipefile)
        self.mkpipe(pipefile)

        f = open(pipefile, 'r')
        while True:
            cmd = f.read(1)
            if not cmd:
                f.close()
                f = open(pipefile, 'r')
            elif cmd == 'n':
                p.next()
            elif cmd == 's':
                if not p.playing:
                    p.play()
            elif cmd == 'p':
                if p.playing:
                    p.pause()
            elif cmd == 'P':
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

    def mkpipe(self, pipefile):
        util.initParent(pipefile)
        if os.path.exists(pipefile):
            os.remove(pipefile)
        os.mkfifo(pipefile, 0600)
        

if __name__ == "__main__":
    l = Listening()
    l.run()
