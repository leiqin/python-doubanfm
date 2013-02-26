#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import os.path
import socket
import logging
import logging.handlers

from util import initParent, readCmdLine, socketfile, \
        encode, inline, EOFflag, resolve
from controller import Controller
import config, source, source.douban

logger = logging.getLogger(__name__)

closed = False
player = None

def init():
    config.init()
    cp = config.load()
    if cp.has_option('global', 'source_manager'):
        cla = cp.get('global', 'source_manager')
        logger.debug(cla)
        cla = resolve(cla)
    else:
        cla = source.SimpleChannelSourceManager
    sources = config.buildSources(cp)
    sm = cla(sources) 
    global player
    player = Controller(sm)
    player.start()
    saveCookieThread = config.SaveCookie()
    saveCookieThread.start()


def start():
    try:
        init()
    except Exception:
        logger.exception(u'初始化时发生异常')
        raise

    try:
        logger.info(u'启动服务')
        s = socket.socket(socket.AF_UNIX)
        initParent(socketfile)
        s.bind(socketfile)
        s.listen(1)

        while not closed:
            con, add = s.accept()
            handler(con)
    except Exception:
        logger.exception(u'处理命令时发生异常')
        raise
    finally:
        if s:
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
            cmd, args = readCmdLine(f)
            if not cmd:
                con.close()
                return
            logger.info(u'处理命令 %s %s', cmd, args)
            if hasattr(cmdHandler, cmd):
                m = getattr(cmdHandler, cmd)
                try:
                    message = m(*args)
                    if not message:
                        f.write('OK\n')
                    else:
                        f.write('VALUE %s\n' % EOFflag)
                        f.write(encode(message))
                        f.write('\n')
                        f.write(EOFflag)
                        f.write('\n')
                except Exception as e:
                    logger.exception(u'处理命令异常 %s %s', cmd, args)
                    f.write('ERROR %s\n' % inline(encode(e)))
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

class CmdHander(object):

    def next(self, *args):
        index = 0
        if args:
            index = int(args[0])
        player.next(index=index)

    def play(self, *args):
        if not player.playing:
            player.play()

    def pause(self, *args):
        if player.playing:
            player.pause()

    def togglePause(self, *args):
        if player.playing:
            player.pause()
        else:
            player.play()

    def favourite(self, *args):
        player.like()

    def unFavourite(self, *args):
        player.unlike()

    def info(self, *args):
        song = player.song
        message = None
        if song:
            message = song.info()
        if message:
            return message
        else:
            return u'没有歌曲正在播放'

    def list(self, *args):
        songs = player.list()
        message = '\n'.join([song.oneline() for song in songs])
        if message:
            return message
        else:
            return u'歌曲列表为空'

    def update(self, *args):
        player.update()

    def channel(self, *args):
        if args:
            player.channel(args[0])
        else:
            return player.listChannel()

    def exit(self, *args):
        global closed
        closed = True
        player.close()

cmdHandler = CmdHander()

if __name__ == "__main__":
    start()
