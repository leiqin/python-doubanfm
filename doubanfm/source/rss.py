# -*- coding: utf-8 -*-

import xml.etree.ElementTree as etree
import threading, os.path, urllib2
import logging

import api
from doubanfm import util, config

logger = logging.getLogger(__name__)

class RSS(api.Source):

    def __init__(self, conf):
        self.config = conf
        name = self.config.get('name')
        if name:
            self.name = util.decode(name)
        else:
            self.name = self.config.name
        self.condition = threading.Condition()

        self.cur_id = None
        self.songs = []
        self.cachedir = os.path.join(config.cachedir, self.config.name)
        util.initDir(self.cachedir)
        self.cur_file = os.path.join(self.cachedir, 'cur')
        if os.path.exists(self.cur_file):
            with open(self.cur_file) as f:
                self.cur_id = util.decode(f.read())
        self.update()

    def update(self):
        th = UpdateSongs(self)
        th.start()

    def next(self):
        if not self.songs:
            return None
        with self.condition:
            song = self.songs.pop(0)
            self._cur(song)
            return song

    def list(self, size=None):
        if not self.songs:
            return []
        if size is None or size <=0:
            return list(self.songs)
        elif size >= len(self.songs):
            return list(self.songs)
        else:
            return self.songs[:size]

    def skip(self, song):
        try:
            self.songs.remove(song)
        except ValueError:
            pass

    def select(self, song):
        self.skip(song)
        with self.condition:
            self._cur(song)

    def close(self):
        self._cur()

    def _cur(self, song=None):
        if song:
            self.cur_id = song.id
        if self.cur_id:
            with open(self.cur_file, 'w') as f:
                f.write(util.encode(self.cur_id))

class UpdateSongs(threading.Thread):

    def __init__(self, source):
        threading.Thread.__init__(self)
        self.daemon = True
        self.source = source

    def run(self):
        try:
            rss = self.source.config.get('rss')
            logger.info(u'更新 rss %s', rss)
            response = urllib2.urlopen(rss)
            tree = etree.parse(response)
            with self.source.condition:
                songs = UpdateSongs.parse(tree, self.source.cur_id)
                if not songs:
                    return
                if not self.source.cur_id:
                    songs = songs[-1:]
                songs = map(self._setSource, songs)
                self.source.songs = songs
        except:
            logger.exception(u'更新 rss 出错 %s', rss)

    def _setSource(self, song):
        song.source = self.source
        return song

    @staticmethod
    def parse(tree, cur_id=None):
        songs = []
        for item in tree.findall('channel/item'):
            song = Song()
            for e in item.findall('enclosure'):
                t = e.get('type')
                if t and t.startswith('audio/'):
                    song.url = e.get('url')
                    break
            else:
                continue
            song.title = item.find('title').text
            song.id = item.find('guid').text
            song.pubDate = item.find('pubDate').text
            logger.debug(song.info())
            if cur_id and song.id == cur_id:
                break
            songs.append(song)
        songs.reverse()
        return songs

class Song(api.Song):

    def __init__(self):
        pass

    def info(self):
        result = []
        result.append('Title     : %s' % self.title)
        result.append('Public    : %s' % self.pubDate)
        if self.source:
            result.append('Source    : %s' % self.source.name)
        if self.time and self.duration:
            result.append('Time      : %s' % util.showtime(self.time))
            result.append('Duration  : %s' % util.showtime(self.duration))
        return '\n'.join(result)

    def oneline(self):
        return self.title


if __name__ == '__main__':
    import sys
    f = urllib2.urlopen(sys.argv[1])
    tree = etree.parse(f)
    songs = UpdateSongs.parse(tree)
    for song in songs:
        print song.info()
        print ''
