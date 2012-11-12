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
cmdpipe = "~/.cache/python-doubanfm/cmdpipe"
infopipe = "~/.cache/python-doubanfm/infopipe"
stdout = "~/.cache/python-doubanfm/stdout"
stderr = "~/.cache/python-doubanfm/stderr"

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

def logerror():
    print sys.exc_info()
    with open(os.path.expanduser(errorfile), 'a') as f:
        f.write(time.strftime('%Y-%m-%d %H:%M:%S'))
        f.write('\n')
        traceback.print_exc(file=f)
        f.write('\n')

