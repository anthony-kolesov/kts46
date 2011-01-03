#!/usr/bin/python
"""
Description:
    Runs all kts46 server processes.

License:
   Copyright 2010-2011 Anthony Kolesov

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import logging, sys, socket, signal
from ConfigParser import SafeConfigParser
from SimpleXMLRPCServer import SimpleXMLRPCServer
from multiprocessing import Process
from optparse import OptionParser
# Project imports
PROJECT_LIB_PATH = '../lib/'
if PROJECT_LIB_PATH not in sys.path:
    sys.path.append(PROJECT_LIB_PATH)
import kts46.utils
from kts46.server.worker import Worker
from kts46.server.rpc import RPCServer
from kts46.server.json_api import JSONApiServer
from kts46.server.supervisor import Supervisor


def startWorker(cfg, id=None):
    worker = Worker(cfg, id)
    worker.run()

def startHTTPServer(cfg):
    apiServer = JSONApiServer(cfg)
    apiServer.serve_forever()

def startSupervisor(cfg):
    supervisor = Supervisor(cfg)
    supervisor.start()


def configureCmdOptions():
    usage = "usage: %prog [options] <server type>*"
    epilog = """<server type> could be: rpc-server, worker, supervisor and/or http."""

    cmdOpts = OptionParser(usage=usage, epilog=epilog)
    cmdOpts.add_option('-i', '--worker-id', action='store', dest='wid', default=None,
                       help='Worker id. Must be unique in a network of workers.')
    return cmdOpts.parse_args(sys.argv[1:])


if __name__ == '__main__':
    cfg = kts46.utils.getConfiguration()
    kts46.utils.configureLogging(cfg)
    logger = logging.getLogger(cfg.get('loggers', 'RPCServer'))
    options, args = configureCmdOptions()

    # Check whether worker is enabled in this instance.
    #if cfg.getboolean('servers', 'worker'):
    if 'worker' in args:
        logger.info('Worker is enabled.')
        p = Process(target=startWorker, args=(cfg, options.wid))
        p.start()
    else:
        logger.info('Worker is disabled.')

    # Start HTTP API server if required.
    if 'http' in args:
        logger.info('HTTP server is enabled.')
        httpServerProcess = Process(target=startHTTPServer, args=(cfg,))
        httpServerProcess.start()
    else:
        logger.info('HTTP server is disabled.')

    # Start supervisor if required.
    if "supervisor" in args:
        logger.info("Supervisor is enabled.")
        supervisorProcess = Process(target=startSupervisor, args=(cfg,))
        supervisorProcess.start()
    else:
        logger.info("Supervisor is disabled.")

    # Check whether RPC server is actually enabled in this instance.
    if 'rpc-server' in args:
        logger.info('RPC server is enabled.')

        # Create and configure server.
        address = cfg.get('rpc-server', 'bind-address')
        port = cfg.getint('rpc-server', 'port')
        try:
            rpcserver = SimpleXMLRPCServer((address, port), allow_none=True)
        except socket.error:
            logger.fatal("Couldn't bind to specified IP address: {0}.".format(address))
            sys.exit(1)

        server = RPCServer(cfg)
        rpcserver.register_instance(server)
        # Run server.
        logger.info('Starting RPC server...')
        rpcserver.serve_forever()
    else:
        logger.info('RPC server is disabled.')
        signal.pause()
