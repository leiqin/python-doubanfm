# -*- coding: utf-8 -*-

import lxml.etree as etree
import logging, urlparse

import rss
from doubanfm import util, config

logger = logging.getLogger(__name__)

class SoundOfHope(rss.RSS):
    '''
    希望之声 http://soundofhope.org
    需要安装 lxml

    配置选项：
        label_l1 (必须) <string> 一级标题 比如：天下纵横
        label_l2 (必须) <string> 二级标题 比如：今日点击
        name (可选) <string> 名称
        update_on_startup (可选) <boolean> 服务启动时更新，默认为 False
        init_count (可选) <int> 第一次更新时保留多少条目，默认为 1
        pre_download (可选) <boolean> 预下载，先下载，后播放，默认为 False
        proxy_enable (可选) <boolean> 是否使用代理，默认为 False
        proxy (可选) <string> 代理，如：http://localhost:8118
        threshold (可选) <int> 当有多个源时，每次该源播放的歌曲数，0 表示放完为止，默认为 1
    '''

    def updateCallable(self):
        return UpdateSongs(self)

class UpdateSongs(rss.UpdateSongs):

    def update(self):
        songs = []
        home = 'http://soundofhope.org'
        label_l1 = util.decode(self.source.conf.get('label_l1'))
        label_l2 = util.decode(self.source.conf.get('label_l2'))
        response = self.opener.open(home, timeout=config.getint('timeout', 30))
        html = etree.parse(response, etree.HTMLParser())
        for l1 in html.findall('//div[@id="nav-site"]/ul/li[a]'):
            a = l1.find('a')
            if a.text.find(label_l1) != -1:
                break
        else:
            logger.warning(u'没有找到一级标签 label_l1 = %s', label_l1)
            return songs

        for l2 in l1.findall('div/ul/li/a'):
            if l2.text.find(label_l2) != -1:
                break
        else:
            logger.warning(u'没有找到二级标签 label_l1 = %s label_l2 = %s', (label_l1, label_l2))
            return songs

        items = urlparse.urljoin(home, l2.get('href'))

        response = self.opener.open(items, timeout=config.getint('timeout', 30))
        html = etree.parse(response, etree.HTMLParser())
        for item in html.findall('//div[@id="CategoryCol_mid"]/div/ul/li/a'):
            url = urlparse.urljoin(items, item.get('href')).strip()
            if self.last_id and self.last_id == url:
                break
            song = rss.Song()
            song.id = url
            song.title = item.text.strip()
            response = self.opener.open(url, timeout=config.getint('timeout', 30))
            html = etree.parse(response, etree.HTMLParser())
            div = html.find('//div[@id="columnfirstnei2"]')
            pubDate = div.find('div[@class="subtitle"]/span[@class="date"]')
            song.pubDate = pubDate.text
            mp3 = div.find('.//div[@class="mp3_links"]/a')
            song.url = urlparse.urljoin(url, mp3.get('href'))
            song.uri = song.url
            songs.append(song)
            if not self.last_id and len(songs) >= self.init_count:
                break

        songs.reverse()
        return songs


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    conf = config.Config()
    conf['label_l1'] = u'天下纵横'
    conf['label_l2'] = u'今日点击'
    conf['init_count'] = 5
    conf['proxy_enable'] = True
    conf['proxy'] = 'http://localhost:8118'
    source = SoundOfHope(conf)
    call = source.updateCallable()
    call()
    for song in source.songs.values():
        print song.info()
        print ''
