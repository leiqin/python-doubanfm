#!/usr/bin/python
# encoding=utf-8

import os
import os.path
import logging

logger = logging.getLogger(__name__)

logfile = os.path.expanduser("~/.cache/python-doubanfm/doubanfm.log")
cookiefile = os.path.expanduser("~/.cache/python-doubanfm/cookies.txt")

socketfile = os.path.expandvars("/tmp/python-doubanfm/$USER/socket")
stdout = os.path.expandvars("/tmp/python-doubanfm/$USER/stdout")
stderr = os.path.expandvars("/tmp/python-doubanfm/$USER/stderr")

EOFflag = 'EOF'

def initParent(filepath):
    dirname = os.path.dirname(filepath)
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

if __name__ == '__main__':
    print stdout
