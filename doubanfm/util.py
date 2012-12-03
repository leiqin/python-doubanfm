#!/usr/bin/python
# encoding=utf-8

import os
import os.path
import threading
import traceback
import time
import sys

errorfile = os.path.expanduser("~/.cache/python-doubanfm/error")
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

def logerror():
    with open(errorfile, 'a') as f:
        f.write(time.strftime('%Y-%m-%d %H:%M:%S'))
        f.write('\n')
        traceback.print_exc(file=f)
        f.write('\n')

if __name__ == '__main__':
    print stdout
