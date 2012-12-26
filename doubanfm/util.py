#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import os.path
import logging

logger = logging.getLogger(__name__)

configdir = '~/.config/python-doubanfm'
cachedir = '~/.cache/python-doubanfm'
cookiefile = os.path.expanduser("~/.cache/python-doubanfm/cookies.txt")

socketfile = os.path.expandvars("/tmp/python-doubanfm/$USER/socket")
stdout = os.path.expandvars("/tmp/python-doubanfm/$USER/stdout")
stderr = os.path.expandvars("/tmp/python-doubanfm/$USER/stderr")

EOFflag = 'EOF'

def initParent(filepath):
    dirname = os.path.dirname(filepath)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)

def initDir(dirname):
    if not os.path.isdir(dirname):
        os.makedirs(dirname)

def initFile(filepath):
    if os.path.isfile(filepath):
        return
    initParent(filepath)
    with open(filepath):
        pass

def readCmdLine(file):
    while True:
        line = file.readline()
        if not line:
            return None, []
        # 忽略空行
        line = line.strip()
        if not line:
            continue
        args = line.split()
        cmd = args.pop(0)
        return cmd, args

def readReplyLine(file):
    while True:
        line = file.readline()
        if not line:
            return None, []
        # 忽略空行
        line = line.strip()
        if not line:
            continue
        args = line.split(None, 1)
        result = args.pop(0)
        message = None
        if args:
            message = args.pop(0)
        return result, message

def readUtilEOFLine(file, EOFflag='EOF'):
    if EOFflag[-1] != '\n':
        EOFflag = EOFflag + '\n'
    arr = []
    while True:
        line = file.readline()
        if not line or line == EOFflag:
            return ''.join(arr)
        arr.append(line)

def encode(string):
    if not string:
        return string
    if type(string) == str:
        return string
    elif type(string) == unicode:
        return string.encode('utf-8')
    else:
        return encode(repr(string))

def decode(string):
    if not string:
        return string
    if type(string) == str:
        return string.decode('utf-8')
    else:
        return string


def inline(message):
    if not message:
        return message
    return message.replace('\n', ' ')

def isInline(message):
    if not message:
        return True
    return not '\n' in message

def showtime(second):
    h = m = s = 0
    s = int(second)
    if s > 60:
        m = s / 60
        s = s % 60
    if m > 60:
        h = m / 60
        m = m % 60
    if h:
        return '%d:%02d:%02d' % (h, m, s)
    else:
        return '%02d:%02d' % (m, s)

def resolve(name):
    """Resolve a dotted name to a global object."""
    # copy from logging.config
    name = name.split('.')
    used = name.pop(0)
    found = __import__(used)
    for n in name:
        used = used + '.' + n
        try:
            found = getattr(found, n)
        except AttributeError:
            __import__(used)
            found = getattr(found, n)
    return found

if __name__ == '__main__':
    print stdout
