# -*- coding: utf-8 -*-

import xml.etree.ElementTree as etree
import threading, os.path, urllib2
import logging
from collections import OrderedDict

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

        self.last_id = None
        self.cur_id = None
        self.songs = OrderedDict()
        self.cachedir = os.path.join(config.cachedir, self.config.name)
        util.initDir(self.cachedir)
        self.cur_file = os.path.join(self.cachedir, 'cur')
        if os.path.exists(self.cur_file):
            with open(self.cur_file) as f:
                self.cur_id = util.decode(f.read()).strip()
        self.updating = False
        update_on_startup = False
        if 'update_on_startup' in self.config:
            update_on_startup = self.config.getboolean('update_on_startup')
        if update_on_startup:
            self.update()

    def update(self):
        if self.updating:
            return
        self.updating = True
        th = UpdateSongs(self)
        th.start()

    def next(self):
        if not self.songs:
            return None
        _, song = self.songs.popitem(last=False)
        self._cur(song)
        return song

    def list(self, size=None):
        songs = self.songs.values()
        if not songs:
            return []
        if size is None:
            return list(songs)
        elif size <=0:
            return []
        else:
            return songs[:size]

    def skip(self, song):
        if song.id in self.songs:
            del self.songs[song.id]

    def select(self, song):
        self.skip(song)
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
            songs = UpdateSongs.parse(tree, self.source.last_id or self.source.cur_id)
            if not songs:
                logger.debug(u'rss 中没有需要更新的内容 %s', rss)
                return
            if not self.source.last_id and not self.source.cur_id:
                songs = songs[-1:]
            for song in songs:
                song.source = self.source
                self.source.songs[song.id] = song
            self.source.last_id = song.id
            logger.debug(u'更新完成 rss %s', rss)
        except:
            logger.exception(u'更新出错 rss %s', rss)
        finally:
            self.source.updating = False

    @staticmethod
    def parse(tree, last_id=None):
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
            song.id = item.find('guid').text.strip()
            song.pubDate = item.find('pubDate').text
            if last_id and song.id == last_id:
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
