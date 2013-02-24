# -*- coding: utf-8 -*-

import xml.etree.ElementTree as etree
import os, os.path, urllib2, copy, pickle
import logging, tempfile
from collections import OrderedDict

import api
from doubanfm import util, config, threadpool

logger = logging.getLogger(__name__)

class RSS(api.Source):
    '''
    配置选项：
        rss (必须) <string> RSS 源的网址
        name (可选) <string> 名称
        update_on_startup (可选) <boolean> 服务启动时更新，默认为 False
        init_count (可选) <int> 第一次更新时保留多少条目，默认为 1
        pre_download (可选) <boolean> 预下载，先下载，后播放，默认为 False
        proxy_enable (可选) <boolean> 是否使用代理，默认为 False
        proxy (可选) <string> 代理，如：http://localhost:8118
        threshold (可选) <int> 当有多个源时，每次该源播放的歌曲数，0 表示放完为止，默认为 1
    '''

    def __init__(self, conf):
        self.conf = conf
        self.name = self.conf.getName()

        self.last_id = None
        self.cur_id = None
        self.song = None
        self.songs = OrderedDict()
        self.cachedir = self.conf.getCacheDir()
        util.initDir(self.cachedir)
        self.cur_file = os.path.join(self.cachedir, 'cur')
        if os.path.exists(self.cur_file):
            with open(self.cur_file) as f:
                self.cur_id = util.decode(f.read()).strip()

        self.pre_download = False
        if 'pre_download' in self.conf:
            self.pre_download = self.conf.getboolean('pre_download')
            self.loadCache()
            self.clearCache()
            self.saveCache()

        self.init_count = 1
        if 'init_count' in self.conf:
            self.init_count = self.conf.getint('init_count')

        self.proxy_enable = False
        self.proxy = None
        if 'proxy_enable' in self.conf:
            self.proxy_enable = self.conf.getboolean('proxy_enable')
        if 'proxy' in self.conf:
            self.proxy = self.conf.get('proxy')

        self.updating = False
        update_on_startup = False
        if 'update_on_startup' in self.conf:
            update_on_startup = self.conf.getboolean('update_on_startup')
        if update_on_startup:
            self.update()

    def update(self):
        call = self.updateCallable()
        threadpool.submit(call)

    def updateCallable(self):
        return UpdateSongs(self)

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
            old = True
            for song in songs:
                song.source = self
                if not self.cur_id:
                    self.songs[song.id] = song
                else:
                    if song.id == self.cur_id:
                        self.song = song
                        old = False
                        continue
                    if not old:
                        self.songs[song.id] = song
            if song:
                self.last_id = song.id
        except Exception:
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

class UpdateSongs(object):

    def __init__(self, source):
        self.source = source
        self.last_id = self.source.last_id or self.source.cur_id
        self.init_count = self.source.init_count
        self.opener = urllib2.build_opener()
        if source.proxy_enable and source.proxy:
            logger.debug(u'使用代理 %s %s' % (source.name, source.proxy))
            self.opener.add_handler(urllib2.ProxyHandler({'http':source.proxy}))

    def __call__(self):
        if self.source.updating:
            return
        self.source.updating = True
        try:
            logger.info(u'更新源 %s', self.source.name)
            songs = self.update()
            if not songs:
                logger.debug(u'%s 中没有需要更新的内容', self.source.name)
                self.source.clearCache()
                return
            for song in songs:
                song.source = self.source
                if self.source.pre_download:
                    self.download(song)
                self.source.songs[song.id] = song
                self.source.saveCache()
            self.source.last_id = song.id
            logger.debug(u'更新完成 %s', self.source.name)
            self.source.clearCache()
        except Exception:
            logger.exception(u'更新出错 %s', self.source.name)
        finally:
            self.source.updating = False
            self.opener.close()

    def download(self, song):
        logger.debug(u'下载歌曲 %s', song.url)
        suffix = util.getSuffix(song.url)
        if not suffix:
            suffix = '.mp3'
        fd, path = tempfile.mkstemp(suffix, '', self.source.cachedir)
        response = self.opener.open(song.url, timeout=config.getint('timeout', 30))
        while True:
            data = response.read(4096)
            if not data:
                break
            os.write(fd, data)
        response.close()
        os.close(fd)
        song.file = path
        logger.debug(u'下载完成 <%s> %s', path, song.url)

    def update(self):
        rss = self.source.conf.get('rss')
        logger.debug(u'解析 rss %s', rss)
        response = self.opener.open(rss, timeout=config.getint('timeout', 30))
        tree = etree.parse(response)
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
            if self.last_id and song.id == self.last_id:
                break
            songs.append(song)
            if not self.last_id and len(songs) >= self.init_count:
                break
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
    logging.basicConfig(level=logging.DEBUG)
    import sys
    rss = sys.argv[1]
    conf = config.Config()
    conf['rss'] = rss
    conf['init_count'] = 5
    source = RSS(conf)
    call = source.updateCallable()
    call()
    for song in source.songs.values():
        print song.info()
        print ''
