#!/usr/bin/python
# encoding=utf-8

import argparse
import os
import os.path
import sys

import listeningfifo
import douban

parser = argparse.ArgumentParser(description="CmdLine for http://douban.fm . you can use cookie file export from firefox by Firecookie, put it to %s" % douban.Douban.cookiefile)

parser.add_argument('-s', '--server', action='store_true', help="Start the server")

parser.add_argument('-p', '--play', action='store_const', const='p', dest="flag", help="Start play")
parser.add_argument('-P', '--pause', action='store_const', const='P', dest="flag", help="Pause")
parser.add_argument('-G', '--toggle-pause', action='store_const', const='G', dest="flag", help="Toggle between play/pause")

parser.add_argument('-n', '--next', action='store_const',const='n',dest="flag", help="Play next song")

parser.add_argument('-f', '--favourite', action='store_const', const='f', dest="flag", help="Like current song")
parser.add_argument('-u', '--unfavourite', action='store_const', const='u', dest="flag", help="Unlike current song")
parser.add_argument('-F', '--toggle-favourite', action='store_const', const='F', dest="flag", help="Toggle between like/unlike")

parser.add_argument('-i', '--info', action='store_true', help="Display current song info")
parser.add_argument('-l', '--list', action='store_true', help="Display song list")

parser.add_argument('-x', '--exit', action='store_true', help="Shutdown the server")

args = parser.parse_args()

def writepipe(ch):
    cmdpipe = listeningfifo.cmdpipe
    if not os.path.exists(cmdpipe):
        print >>sys.stderr, 'Server is not start'
        return False
    with open(cmdpipe, 'w') as p:
        p.write(ch)
        return True

if args.exit:
    writepipe('x')
elif args.server:
    listeningfifo.start()
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
elif args.flag:
    writepipe(args.flag)
else:
    parser.print_help()

