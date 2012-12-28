# -*- coding: utf-8 -*-

import xml.etree.ElementTree as etree
import threading, os, os.path, urllib2, copy, pickle
import logging, tempfile
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
        self.song = None
        self.songs = OrderedDict()
        self.cachedir = os.path.join(config.cachedir, self.config.name)
        util.initDir(self.cachedir)
        self.cur_file = os.path.join(self.cachedir, 'cur')
        if os.path.exists(self.cur_file):
            with open(self.cur_file) as f:
                self.cur_id = util.decode(f.read()).strip()

        self.pre_download = False
        if 'pre_download' in self.config:
            self.pre_download = self.config.getboolean('pre_download')
        self.loadCache()
        self.clearCache()
        self.saveCache()

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

    def loadCache(self):
        if not self.pre_download:
            return
        cachefile = os.path.join(self.cachedir, 'cache')
        if not os.path.exists(cachefile):
            return
        try:
            logger.debug(u'歌曲源 <%s> 加载缓存', self.name)
            with open(cachefile, 'rb') as f:
                songs = pickle.load(f)
            for song in songs:
                song.source = self
                if not self.cur_id:
                    self.songs[song.id] = song
                else:
                    old = True
                    if song.id == self.cur_id:
                        self.song = song
                        old = False
                        continue
                    if not old:
                        self.songs[song.id] = song
            if song:
                self.last_id = song.id
        except:
            logger.exception(u'加载缓存出错 %s', cachefile)

    def saveCache(self):
        if not self.pre_download:
            return
        cachefile = os.path.join(self.cachedir, 'cache')
        songs = []
        if self.song:
            song = copy.copy(self.song)
            song.source = None
            songs.append(song)
        for song in self.songs.values():
            song = copy.copy(song)
            song.source = None
            songs.append(song)
        if not songs:
            return
        logger.debug(u'歌曲源 <%s> 保存缓存', self.name)
        with open(cachefile, 'wb') as f:
            pickle.dump(songs, f)

    def clearCache(self):
        if not self.pre_download:
            return
        fs = set(['cur', 'cache'])
        if self.song:
            if self.song.file:
                fs.add(os.path.basename(self.song.file))
        for song in self.songs.values():
            if song.file:
                fs.add(os.path.basename(song.file))
        files = os.listdir(self.cachedir)
        for f in files:
            if f in fs:
                continue
            logger.debug(u'清理缓存 %s', f)
            os.remove(os.path.join(self.cachedir, f))

    def _cur(self, song=None):
        if song:
            self.song = song
            self.cur_id = song.id
        if self.cur_id:
            with open(self.cur_file, 'w') as f:
                f.write(util.encode(self.cur_id))

class UpdateSongs(threading.Thread):

    def __init__(self, source):
        threading.Thread.__init__(self)
        self.daemon = True
        self.source = source
        self.opener = urllib2.build_opener()

    def run(self):
        try:
            rss = self.source.config.get('rss')
            logger.info(u'更新 rss %s', rss)
            response = self.opener.open(rss)
            tree = etree.parse(response)
            songs = UpdateSongs.parse(tree, self.source.last_id or self.source.cur_id)
            if not songs:
                logger.debug(u'rss 中没有需要更新的内容 %s', rss)
                self.source.clearCache()
                return
            if not self.source.last_id and not self.source.cur_id:
                songs = songs[-1:]
            for song in songs:
                song.source = self.source
                if self.source.pre_download:
                    self.download(song)
                self.source.songs[song.id] = song
                self.source.saveCache()
            self.source.last_id = song.id
            logger.debug(u'更新完成 rss %s', rss)
            self.source.clearCache()
        except:
            logger.exception(u'更新出错 rss %s', rss)
        finally:
            self.source.updating = False
            self.opener.close()

    def download(self, song):
        logger.debug(u'下载歌曲 %s', song.url)
        suffix = util.getSuffix(song.url)
        if not suffix:
            suffix = '.mp3'
        fd, path = tempfile.mkstemp(suffix, '', self.source.cachedir)
        response = self.opener.open(song.url)
        while True:
            data = response.read(4096)
            if not data:
                break
            os.write(fd, data)
        response.close()
        os.close(fd)
        song.file = path
        logger.debug(u'下载完成 <%s> %s', path, song.url)

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
