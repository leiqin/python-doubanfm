# -*- coding:utf-8 -*-

import gobject
gobject.threads_init()
import pygst
pygst.require('0.10')
import gst, sys, time
import thread
import logging

import api

logger = logging.getLogger(__name__)

class GstPlayer(api.Player):

    def __init__(self):
        self.player = gst.element_factory_make('playbin', None)
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect('message' , self.on_message)
        self.loop = gobject.MainLoop()
        thread.start_new_thread(self.loop.run, ())


    def on_message(self, bus, message):
        try:
            t = message.type
            if t == gst.MESSAGE_EOS:
                self.player.set_state(gst.STATE_PAUSED)
                self.on_eos()
            elif t == gst.MESSAGE_ERROR:
                self.player.set_state(gst.STATE_NULL)
                err, debug = message.parse_error()
                logger.error("Error: %s" % err, debug)
        except Exception:
            logger.exception(u'on_eos 发生异常')
            raise

    def play(self, uri=None, seek=None):
        if uri:
            if not gst.uri_is_valid(sys.argv[1]):
                uri = 'file://' + uri
            self.player.set_state(gst.STATE_NULL)
            self.player.set_property('uri', uri)
            self.player.set_state(gst.STATE_PLAYING)
        if seek:
            time.sleep(0.1)
            self.seek(seek)
        if gst.STATE_PAUSED == self.player.get_state()[1]:
            self.player.set_state(gst.STATE_PLAYING)

    def seek(self, seek=None):
        if not seek:
            return True
        event = gst.event_new_seek(1.0, gst.FORMAT_TIME,
            gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_ACCURATE,
            gst.SEEK_TYPE_SET, seek,
            gst.SEEK_TYPE_NONE, 0)
        return self.player.send_event(event)

    def pause(self):
        if gst.STATE_PLAYING == self.player.get_state()[1]:
            self.player.set_state(gst.STATE_PAUSED)

    @property
    def time(self):
        first = True
        while self.available:
            try:
                position, format = self.player.query_position(gst.FORMAT_TIME)
                return position
            except gst.QueryError:
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
                duration, format = self.player.query_duration(gst.FORMAT_TIME)
                return duration
            except gst.QueryError:
                if first:
                    first = False
                    time.sleep(0.1)
                    continue
                else:
                    return 0

    @property
    def playing(self):
        return gst.STATE_PLAYING == self.player.get_state()[1]

    def available(self):
        state = self.player.get_state()[1]
        return state in (gst.STATE_PLAYING, gst.STATE_PAUSED)

    def close(self):
        self.player.set_state(gst.STATE_NULL)
        self.loop.quit()


if __name__ == '__main__':
    if gst.uri_is_valid(sys.argv[1]):
        uri = sys.argv[1]
    else:
        uri = 'file://' + sys.argv[1]
    seek = None
    if len(sys.argv) >= 3:
        seek = int(sys.argv[2]) * 1000 * 1000 * 1000
    player = GstPlayer()
    player.play(uri, seek)
    print player.duration
    print player.time
    time.sleep(10)

