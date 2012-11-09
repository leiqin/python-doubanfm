#!/usr/bin/python
# encoding=utf-8

import os
import os.path
import codecs

import util


cmdpipe = os.path.expanduser("~/.cache/python-doubanfm/cmdpipe")
infopipe = os.path.expanduser("~/.cache/python-doubanfm/infopipe")

def start():

    # 加快命令行的响应速度
    from player import Player
    player = Player()
    player.play()
    player.start()

    mkpipe(cmdpipe)
    mkpipe(infopipe)

    cmdreader = open(cmdpipe, 'r')
    while True:
        cmd = cmdreader.read(1)
        if not cmd:
            cmdreader.close()
            cmdreader = open(cmdpipe, 'r')
        elif cmd == 'n':
            player.next()
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
            player.exit()
            os.remove(cmdpipe)
            os.remove(infopipe)
            return
        elif cmd == 'i':
            song = player.song
            with codecs.open(infopipe, 'w', 'utf-8') as infowriter:
                print >>infowriter, 'Title    : %s' % song.title
                print >>infowriter, 'Artist   : %s' % song.artist
                print >>infowriter, 'Like     : %s' % song.like
                print >>infowriter, 'Album    : %s' % song.album
                print >>infowriter, 'Year     : %s' % song.publicTime
        elif cmd == 'l':
            song = player.song
            songs = player.douban.songs
            with codecs.open(infopipe, 'w', 'utf-8') as listwriter:
                print >>listwriter, '%s <%s>' % (song.title, song.artist)
                for s in songs:
                    print >>listwriter, '%s <%s>' % (s.title, s.artist)

def mkpipe(pipefile):
    util.initParent(pipefile)
    if os.path.exists(pipefile):
        os.remove(pipefile)
    os.mkfifo(pipefile, 0600)
        

if __name__ == "__main__":
    start()
