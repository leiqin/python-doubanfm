# -*- coding:utf-8 -*-

class Player(object):

    time = 0
    duration = 0
    playing = False

    def play(self, uri=None, seek=None):
        raise NotImplementedError

    def pause(self):
        raise NotImplementedError

    def seek(self, seek=None):
        '''
        seek 的单位是 nanosecond
        '''
        return False

    def on_eos(self):
        pass

    def close(self):
        pass

