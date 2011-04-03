#!/usr/bin/python
# -*- coding: UTF-8 -*-

from flup.server.fcgi import WSGIServer
from kts46.server.webui import DataAPIHandler, ManagementAPIHandler
import kts46.utils
from kts46.server.status import StatusServer
from kts46.server.database import DatabaseServer

# Create ConfigParser
# configFiles = []
# if len(options.cfg) != 0: configFiles.append(options.cfg)
cfg = kts46.utils.getConfiguration([]) # configFiles)
#if options.quite is not None:
#    cfg.set('log', 'quite', str(options.quite))

statusServer = StatusServer(cfg)
dbServer = DatabaseServer(cfg)

dh = DataAPIHandler(statusServer)
mh = ManagementAPIHandler(cfg, dbServer, statusServer)
dataAddress = cfg.get("FastCGI", "dataAddress")
rpcAddress = cfg.get("FastCGI", "JSONRPCAddress")

def app(environ, startResponse):
    sfn = environ["SCRIPT_FILENAME"]
    if sfn == dataAddress:
        return dh.handle(environ, startResponse)
    elif sfn == rpcAddress:
        return mh.handle(environ, startResponse)
    else:
        startResponse('404 Not found', [("Content-Type", "text/plain")])
        #for k, v in environ.iteritems():
        #    print("%s -> %s" % (k, v))
        return ""

WSGIServer(app, bindAddress=cfg.get("FastCGI", "socket"), umask=0000,
           multithreaded=True, multiprocess=True).run()
