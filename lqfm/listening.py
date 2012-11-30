#!/usr/bin/python
# encoding=utf-8

import os
import os.path
import codecs
import socket

import lqfm.util
from lqfm.player import Player

socketfile = lqfm.util.expand(lqfm.util.socketfile)


def start(play=True):

    try:
        player = Player()
        if (play):
            player.play()
        player.start()

        s = socket.socket(socket.AF_UNIX)
        lqfm.util.initParent(socketfile)
        s.bind(socketfile)
        s.listen(1)

        while True:
            con, add = s.accept()

            cmd = con.recv(1)
            if not cmd:
                pass
            elif cmd == 'n':
                index = con.recv(1)
                index = ord(index)
                player.next(index=index)
            elif cmd == 'p':
                if not player.playing:
                    player.play()
            elif cmd == 'P':
                if player.playing:
                    player.pause()
            elif cmd == 'G':
                if player.playing:
                    player.pause()
                else:
                    player.play()
            elif cmd == 'f':
                if not player.song.like:
                    player.like()
            elif cmd == 'u':
                if player.song.like:
                    player.unlike()
            elif cmd == 'F':
                if player.song.like:
                    player.unlike()
                else:
                    player.like()
            elif cmd == 'x':
                s.close()
                cleansocket()
                player.close()
                return
            elif cmd == 'i':
                song = player.song
                if song:
                    con.sendall(song.info().encode('utf-8'))
            elif cmd == 'l':
                songs = player.list()
                for song in songs:
                    con.sendall(song.oneline().encode('utf-8'))
                    con.sendall("\n")
            con.close()
    except:
        lqfm.util.logerror()
        raise
    finally:
        s.close()
        cleansocket()
        player.close()

def cleansocket():
    if os.path.exists(socketfile):
        os.remove(socketfile)

if __name__ == "__main__":
    start()
