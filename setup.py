# coding=utf-8

from distutils.core import setup
import py2exe

setup(console=['srs.py'], 
      data_files=[('',
                   ['config.ini', 
                    'SearchResultStatistics.bat', 
                    '说明.txt'.decode('utf-8').encode('gbk'), 
                    '版本变更说明.txt'.decode('utf-8').encode('gbk')])])