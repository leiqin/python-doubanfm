# -*- coding:utf-8 -*-

import sys
import time
import thread
import threading
import logging
import os
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject
Gst.init(None)

from .api import Player

logger = logging.getLogger(__name__)


class GstPlayer(Player):
    def __init__(self):
        self.player = Gst.ElementFactory.make("playbin", None)

        # 设置 playbin 的 video-sink 为一个伪造的 sink，避免在播放视频时弹窗
        # (PS: 有些 豆瓣FM 的广告是视频的)
        # http://pygstdocs.berlios.de/pygst-tutorial/playbin.html
        fakesink = Gst.ElementFactory.make("fakesink", "fakesink")
        self.player.set_property("video-sink", fakesink)

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_message)
        self.loop = GObject.MainLoop()

        def target():
            try:
                self.loop.run()
            except KeyboardInterrupt:
                logger.info('KeyboardInterrupt in GObject Loop')
                self.close()
                try:
                    import doubanfm.util
                    doubanfm.util.sendExitIfNeed()
                except Exception:
                    logger.exception('')

        thread.start_new_thread(target, ())

    def on_message(self, bus, message):
        try:
            t = message.type
            if t == Gst.MessageType.EOS:
                self.player.set_state(Gst.State.PAUSED)
                self.on_eos()
            elif t == Gst.MessageType.ERROR:
                self.player.set_state(Gst.State.NULL)
                err, debug = message.parse_error()
                logger.error("Error: %s %s" % (err, debug))
                self.on_err()
        except Exception:
            logger.error(u'on_eos 发生异常', exc_info=True)
            raise

    def play(self, uri=None, seek=None):
        if uri:
            if not Gst.uri_is_valid(uri):
                uri = 'file://' + uri
            logger.debug(uri)
            self.player.set_state(Gst.State.NULL)
            self.player.set_property('uri', uri)
            self.player.set_state(Gst.State.PLAYING)
        if seek is not None:
            # 由于 gstreamer 的 seek , query_position 和 query_duration 
            # 都是异步的，是通过消息来通信的，刚刚设置好就操作，
            # 很可能会失败，所以休息 0.1 秒
            time.sleep(0.1)
            self.seek(seek)
        if Gst.State.PAUSED == self.player.get_state(Gst.CLOCK_TIME_NONE)[1]:
            self.player.set_state(Gst.State.PLAYING)

    def seek(self, seek=None):
        if seek is None:
            return True
        # 转换成纳秒
        seek = int(seek * 1000 * 1000 * 1000)
        event = Gst.Event.new_seek(1.0, Gst.Format.TIME, Gst.SeekFlags.FLUSH
                                   | Gst.SeekFlags.ACCURATE, Gst.SeekType.SET,
                                   seek, Gst.SeekType.NONE, 0)
        return self.player.send_event(event)

    def pause(self):
        if Gst.State.PLAYING == self.player.get_state(Gst.CLOCK_TIME_NONE)[1]:
            self.player.set_state(Gst.State.PAUSED)

    @property
    def time(self):
        first = True
        while self.available:
            try:
                ok, position = self.player.query_position(Gst.Format.TIME)
                return position / 1000.0 / 1000 / 1000
            #except Gst.QueryError:
            except Exception:
                logger.error(u'exception in time', exc_info=True)
                if first:
                    first = False
                    time.sleep(0.1)
                    continue
                else:
                    return 0

    @property
    def duration(self):
        first = True
        while self.available:
            try:
                ok, duration = self.player.query_duration(Gst.Format.TIME)
                return duration / 1000.0 / 1000 / 1000
            #except Gst.QueryError:
            except Exception:
                logger.error(u'exception in time', exc_info=True)
                if first:
                    first = False
                    time.sleep(0.1)
                    continue
                else:
                    return 0

    @property
    def playing(self):
        return Gst.State.PLAYING == self.player.get_state(Gst.CLOCK_TIME_NONE)[1]

    def available(self):
        state = self.player.get_state(Gst.CLOCK_TIME_NONE)[1]
        return state in (Gst.State.PLAYING, Gst.State.PAUSED)

    def close(self):
        self.player.set_state(Gst.State.NULL)
        self.loop.quit()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    uri = sys.argv[1]
    seek = None
    if len(sys.argv) >= 3:
        seek = int(sys.argv[2])
    player = GstPlayer()
    player.play(uri, seek)
    print player.duration
    while player.available():
        try:
            print player.time
            time.sleep(3)
        except Exception:
            logger.error('main exception', exc_info=True)
            break
