#!/usr/bin/python
# encoding=utf-8

import os
import os.path
import codecs

import util
from player import Player

cmdpipe = util.expand(util.cmdpipe)
infopipe = util.expand(util.infopipe)

def start(play=True):

    try:
        player = Player()
        if (play):
            player.play()
        player.start()

        mkpipe()

        cmdreader = open(cmdpipe, 'r')
        while True:
            cmd = cmdreader.read(1)
            if not cmd:
                cmdreader.close()
                cmdreader = open(cmdpipe, 'r')
            elif cmd == 'n':
                index = cmdreader.read(1)
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
                player.close()
                clearpipe()
                return
            elif cmd == 'i':
                song = player.song
                with codecs.open(infopipe, 'w', 'utf-8') as infowriter:
                    if song:
                        print >>infowriter, 'Title    : %s' % song.title
                        print >>infowriter, 'Artist   : %s' % song.artist
                        print >>infowriter, 'Like     : %s' % song.like
                        print >>infowriter, 'Album    : %s' % song.album
                        print >>infowriter, 'Public   : %s' % song.publicTime
                        print >>infowriter, 'Time     : %.2f' % player.player.time
                        print >>infowriter, 'Length   : %.2f' % song.length
            elif cmd == 'l':
                song = player.song
                songs = player.douban.songs
                with codecs.open(infopipe, 'w', 'utf-8') as listwriter:
                    if song:
                        print >>listwriter, '%s <%s>' % (song.title, song.artist)
                    for s in songs:
                        print >>listwriter, '%s <%s>' % (s.title, s.artist)
    except:
        util.logerror()
        raise
    finally:
        clearpipe()
        player.close()

def clearpipe():
    for pipe in [cmdpipe, infopipe]:
        if os.path.exists(pipe):
            os.remove(pipe)

def mkpipe():
    for pipe in [cmdpipe, infopipe]:
        util.initParent(pipe)
        if os.path.exists(pipe):
            os.remove(pipe)
        os.mkfifo(pipe, 0600)
        

if __name__ == "__main__":
    start()
