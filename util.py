#!/usr/bin/python
# encoding=utf-8

import os
import os.path
import threading
import traceback
import time
import sys

errorfile = os.path.expanduser('~/.cache/python-doubanfm/error')
cookiefile = os.path.expanduser("~/.cache/python-doubanfm/cookies.txt")
cmdpipe = os.path.expanduser("~/.cache/python-doubanfm/cmdpipe")
infopipe = os.path.expanduser("~/.cache/python-doubanfm/infopipe")

def initParent(filepath):
    dirname = os.path.dirname(filepath)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)

def initFile(filepath):
    if os.path.isfile(filepath):
        return
    initParent(filepath)
    f = open(filepath)
    f.close()

_lock =threading.Lock()

def logerror():
    print sys.exc_info()
    with open(errorfile, 'a') as f:
        f.write(time.ctime())
        f.write('\n')
        traceback.print_exc(file=f)
        f.write('\n')
