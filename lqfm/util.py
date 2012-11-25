#!/usr/bin/python
# encoding=utf-8

import os
import os.path
import threading
import traceback
import time
import sys

errorfile = "~/.cache/python-doubanfm/error"
cookiefile = "~/.cache/python-doubanfm/cookies.txt"

cmdpipe = "/tmp/python-doubanfm/$USER/cmdpipe"
infopipe = "/tmp/python-doubanfm/$USER/infopipe"
stdout = "/tmp/python-doubanfm/$USER/stdout"
stderr = "/tmp/python-doubanfm/$USER/stderr"

def expand(path):
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    return path

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

def logerror():
    print sys.exc_info()
    with open(expand(errorfile), 'a') as f:
        f.write(time.strftime('%Y-%m-%d %H:%M:%S'))
        f.write('\n')
        traceback.print_exc(file=f)
        f.write('\n')

if __name__ == '__main__':
    print expand(stdout)
