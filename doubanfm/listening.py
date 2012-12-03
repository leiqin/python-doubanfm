#!/usr/bin/python
# encoding=utf-8

import os
import os.path
import socket

import doubanfm.util
from doubanfm.player import Player

socketfile = doubanfm.util.socketfile
closed = False
player = None

def initPlayer(play=True):
    global player
    player = Player()
    if (play):
        player.play()
    player.start()

def start(play=True):

    try:
        initPlayer(play)

        s = socket.socket(socket.AF_UNIX)
        doubanfm.util.initParent(socketfile)
        s.bind(socketfile)
        s.listen(1)

        while not closed:
            con, add = s.accept()
            handler(con)
    except:
        doubanfm.util.logerror()
        raise
    finally:
        s.close()
        close()

def close():
    if os.path.exists(socketfile):
        os.remove(socketfile)
    if player:
        player.close()

def handler(con):
    try:
        f = con.makefile('rw')
        while not closed:
            cmd, args = doubanfm.util.readCmdLine(f)
            if not cmd:
                con.close()
                return
            if hasattr(cmdHandler, cmd):
                m = getattr(cmdHandler, cmd)
                try:
                    result, message = m(*args)
                    if result:
                        if not message:
                            f.write('OK\n')
                        else:
                            f.write('VALUE %s\n' % doubanfm.util.EOFflag)
                            f.write(message.encode('utf-8'))
                            f.write('\n')
                            f.write(doubanfm.util.EOFflag)
                            f.write('\n')
                    else:
                        f.write('FAIL %s\n' % inline(message))
                except:
                    doubanfm.util.logerror()
                    f.write('ERROR\n')
            else:
                f.write('ERROR unknow cmd %s\n' % cmd)
            f.flush()
    except socket.error as e:
        if e.errno == 32:
            # Broken pipe
            # 连接断开
            pass
        else:
            raise
    finally:
        con.close()

def inline(message):
    if not message:
        return message
    return message.replace('\n', ' ')

class CmdHander(object):

    def next(self, *args):
        index = 0
        if args:
            index = int(args[0])
        player.next(index=index)
        return True, ''

    def play(self, *args):
        if not player.playing:
            player.play()
        return True, ''

    def pause(self, *args):
        if player.playing:
            player.pause()
        return True, ''

    def togglePause(self, *args):
        if player.playing:
            player.pause()
        else:
            player.play()
        return True, ''

    def favourite(self, *args):
        player.like()
        return True, ''

    def unFavourite(self, *args):
        player.unlike()
        return True, ''

    def info(self, *args):
        song = player.song
        message = None
        if song:
            message = song.info()
        return True, message

    def list(self, *args):
        songs = player.list()
        message = '\n'.join([song.oneline() for song in songs])
        return True, message

    def exit(self, *args):
        global closed
        closed = True
        player.close()
        return True, ''

cmdHandler = CmdHander()

if __name__ == "__main__":
    start()
