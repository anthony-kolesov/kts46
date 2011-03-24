#!/usr/bin/python
# -*- coding: UTF-8 -*-

from cgi import escape
import sys, os
from flup.server.fcgi import WSGIServer
from kts46.server.webui import DataAPIHandler, ManagementAPIHandler
import kts46.utils

# Create ConfigParser
# configFiles = []
# if len(options.cfg) != 0: configFiles.append(options.cfg)
cfg = kts46.utils.getConfiguration([]) # configFiles)
#if options.quite is not None:
#    cfg.set('log', 'quite', str(options.quite))

dh = DataAPIHandler(cfg)
mh = ManagementAPIHandler(cfg)

def app(environ, startResponse):
    sfn = environ["SCRIPT_FILENAME"]
    if sfn == "/api/data":
        return dh.handle(environ, startResponse)
    elif sfn == "/api/jsonrpc":
        return mh.handle(environ, startResponse)
    else:
        startResponse('200 OK', [("Content-Type", "text/plain")])
        for k, v in environ.iteritems():
            print("%s -> %s" % (k, v))
        return ""

WSGIServer(app, bindAddress="/tmp/kts46_fcgi.socket", umask=0000).run()
