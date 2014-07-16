#!/usr/bin/env python
#coding: utf-8
#file   : gen_conf.py
#author : ning
#date   : 2013-12-20 09:36:42

import urllib, urllib2
import os, sys
import re, time
import logging
from pcl import common

from string import Template as T
T.s = T.substitute

CLUSTER_NAME = 'cluster0'
BASEDIR = '/tmp/r'
HOSTS = [
        '127.0.0.5',
        '127.0.0.5',
        ]
MASTER_PER_MACHINE = 2

# gen the "redis" section
port = 2000
for i in range(len(HOSTS)):
    for j in range(MASTER_PER_MACHINE):
        slave_port = port + 1000

        m = HOSTS[i]
        s = HOSTS[(i+1)%len(HOSTS)]

        #old format
        #templete = "('$m:$port', '$BASEDIR/redis-$port'), ('$s:$slave_port', '$BASEDIR/redis-$slave_port'),"

        #new format:
        master_name = '%s-%s' % (CLUSTER_NAME, port)
        templete = "'$master_name:$m:$port:$BASEDIR/redis-$port', '$master_name:$s:$slave_port:$BASEDIR/redis-$slave_port',"
        print T(templete).s(globals())
        port += 1

# gen the "nutcracker" section
port = 4000
for i in range(len(HOSTS)):
    m = HOSTS[i]
    for j in range(MASTER_PER_MACHINE):
        xport = port + j
        templete = "('$m:$xport', '$BASEDIR/nutcracker-$xport'),"
        print T(templete).s(globals())

