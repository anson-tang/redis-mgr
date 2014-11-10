#!/usr/bin/env python
#coding: utf-8
#file   : web.py
#author : ning
#date   : 2014-01-22 08:28:23

from utils import *

PWD = os.path.dirname(os.path.realpath(__file__))
WORKDIR = os.path.join(PWD, '../')


import mimetypes
import CGIHTTPServer
from SocketServer import ThreadingMixIn
from SocketServer import ForkingMixIn
from BaseHTTPServer import HTTPServer
socket.setdefaulttimeout(60)

class MultiThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

class WebServer():
    '''
    please use scheduler instead.
    '''
    def _web_server(self, port=8008):
        server_address = ('', int(port))
        handler = CGIHTTPServer.CGIHTTPRequestHandler
        cgipath = os.path.join(PWD, '../cgi')
        handler.cgi_directories = ['/cgi', cgipath]
        server = MultiThreadedHTTPServer(server_address, handler)

        server.serve_forever()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4


