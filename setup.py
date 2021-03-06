#!/usr/bin/python
# encoding=utf-8

from distutils.core import setup

version = '4.0'

setup(name='python-doubanfm',
      version=version,
      description='CommandLine for http://douban.fm',
      long_description='''
        命令行的 http://douban.fm
      ''',
      author='leiqin',
      author_email='leiqin2010@gmail.com',
      url='https://github.com/leiqin/python-doubanfm',
      packages=['doubanfm', 'doubanfm.source', 'doubanfm.player'],
      package_data={'doubanfm': ['*.conf']},
      scripts=['fm'],
      license='LGPL-3+',
      requires=['gst', 'lxml'], )
