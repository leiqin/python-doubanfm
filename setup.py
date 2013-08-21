#!/usr/bin/python
# encoding=utf-8

from distutils.core import setup

version = '3.3'

setup(name='python-doubanfm',
      version=version,
      description='CommandLine for http://douban.fm',
      long_description='''
        命令行的 http://douban.fm
      ''',
      author='leiqin',
      author_email='leiqin2010@gmail.com',
      url='https://github.com/leiqin/python-doubanfm',
      packages=['doubanfm', 'doubanfm.source'],
      package_data={'doubanfm': ['*.conf']},
      scripts=['fm'],
      license='LGPL-3+',
      requires=['gst','lxml'],
      )
