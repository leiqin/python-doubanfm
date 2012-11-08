#!/usr/bin/python
# encoding=utf-8

import argparse
import os
import os.path

import listeningfifo
import douban

parser = argparse.ArgumentParser(description="CmdLine for http://douban.fm . you can use cookie file export from firefox , put it to %s" % douban.Douban.cookiefile)

parser.add_argument('-s', '--server', action='store_true', help="Start the server")

parser.add_argument('-p', '--play', action='store_const', const='p', dest="flag", help="Start play")
parser.add_argument('-P', '--pause', action='store_const', const='P', dest="flag", help="Pause")
parser.add_argument('-G', '--toggle-pause', action='store_const', const='G', dest="flag", help="Toggle between play/pause")

parser.add_argument('-n', '--next', action='store_const',const='n',dest="flag", help="Play next song")

parser.add_argument('-l', '--like', action='store_const', const='l', dest="flag", help="Like current song")
parser.add_argument('-u', '--unlike', action='store_const', const='u', dest="flag", help="Unlike current song")
parser.add_argument('-L', '--toggle-like', action='store_const', const='L', dest="flag", help="Toggle between like/unlike")

parser.add_argument('-x', '--exit', action='store_true', help="Shutdown the server")

args = parser.parse_args()

def writepipe(ch):
    pipefile = listeningfifo.pipefile
    with open(pipefile, 'w') as p:
        p.write(ch)

if args.exit:
    writepipe('x')
elif args.server:
    listeningfifo.start()
elif args.flag:
    writepipe(args.flag)
else:
    parser.print_help()

