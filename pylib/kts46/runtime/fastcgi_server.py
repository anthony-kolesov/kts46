#!/usr/bin/python
# -*- coding: UTF-8 -*-

from cgi import escape
import sys, os
from flup.server.fcgi import WSGIServer
from kts46.server.webui import DataAPIHandler
import kts46.utils

# Create ConfigParser
# configFiles = []
# if len(options.cfg) != 0: configFiles.append(options.cfg)
cfg = kts46.utils.getConfiguration([]) # configFiles)
#if options.quite is not None:
#    cfg.set('log', 'quite', str(options.quite))

dh = DataAPIHandler(cfg)


def app(environ, startResponse):
    if environ["SCRIPT_NAME"] == "/api/data":
        return dh.handle(environ, startResponse)
    else:
        return dh.handle(environ, startResponse)

WSGIServer(app, bindAddress="/tmp/kts46_fcgi.socket", umask=0000).run()
