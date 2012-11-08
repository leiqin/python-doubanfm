#!/usr/bin/python
# encoding=utf-8

import os
import os.path

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
