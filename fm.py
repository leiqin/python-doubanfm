#!/usr/bin/python
# encoding=utf-8

import argparse
import os
import os.path
import sys

import listeningfifo
import douban

parser = argparse.ArgumentParser(description="命令行的 豆瓣FM ，可以使用 Firecookie(firefox 的插件) 导出的 cookie 文件，文件路径为 %s " % douban.Douban.cookiefile)

parser.add_argument('-s', '--server', action='store_const', const=1, dest='server', help="启动服务，并开始播放")
parser.add_argument('-U', '--unplay-server', action='store_const', const=2, dest='server', help="仅启动服务")

parser.add_argument('-p', '--play', action='store_const', const='p', dest="flag", help="播放")
parser.add_argument('-P', '--pause', action='store_const', const='P', dest="flag", help="暂停")
parser.add_argument('-G', '--toggle-pause', action='store_const', const='G', dest="flag", help="播放/暂停")

parser.add_argument('-n', '--next', action='store',nargs='?', const=0, type=int, help="下一首歌曲，可以指定播放第 n 首歌曲，如果 n 为 0 或者 n 超过歌曲列表长度，则会获取新的歌曲列表，这是 豆瓣FM 默认的行为，如果不指定 n 默认为 0")

parser.add_argument('-f', '--favourite', action='store_const', const='f', dest="flag", help="喜欢")
parser.add_argument('-u', '--unfavourite', action='store_const', const='u', dest="flag", help="不喜欢")
parser.add_argument('-F', '--toggle-favourite', action='store_const', const='F', dest="flag", help="喜欢/不喜欢")

parser.add_argument('-i', '--info', action='store_true', help="当前歌曲信息")
parser.add_argument('-l', '--list', action='store_true', help="歌曲列表")

parser.add_argument('-x', '--exit', action='store_const', const='x', dest="flag", help="关闭服务")

args = parser.parse_args()

def writepipe(ch):
    cmdpipe = listeningfifo.cmdpipe
    if not os.path.exists(cmdpipe):
        print >>sys.stderr, '服务尚未启动'
        return False
    with open(cmdpipe, 'w') as p:
        p.write(ch)
        return True

if args.server:
    if args.server == 1:
        listeningfifo.start()
    else:
        listeningfifo.unplaystart()
elif args.info:
    if writepipe('i'):
        infopipe = listeningfifo.infopipe
        with open(infopipe, 'r') as p:
            print p.read()
elif args.list:
    if writepipe('l'):
        infopipe = listeningfifo.infopipe
        with open(infopipe, 'r') as p:
            print p.read()
elif args.next is not None:
    index = int(args.next)
    index = min(255 , index)
    index = max(0 , index)
    flag = 'n' + chr(index)
    writepipe(flag)
elif args.flag:
    writepipe(args.flag)
else:
    parser.print_help()

