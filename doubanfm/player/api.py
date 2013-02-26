# -*- coding:utf-8 -*-

class Player(object):
    '''
    time, duration, seek 以秒为单位
    '''

    time = 0
    duration = 0
    playing = False

    def play(self, uri=None, seek=None):
        raise NotImplementedError

    def pause(self):
        raise NotImplementedError

    def seek(self, seek=None):
        return False

    def on_eos(self):
        pass

    def on_err(self):
        pass

    def close(self):
        pass

