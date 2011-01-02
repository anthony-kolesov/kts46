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

import logging, sys, socket
from ConfigParser import SafeConfigParser
from SimpleXMLRPCServer import SimpleXMLRPCServer
from multiprocessing import Process
# Project imports
PROJECT_LIB_PATH = '../lib/'
if PROJECT_LIB_PATH not in sys.path:
    sys.path.append(PROJECT_LIB_PATH)
import kts46.utils
from kts46.server.worker import Worker
from kts46.server.rpc import RPCServer


def startWorker(cfg):
    worker = Worker(cfg)
    worker.run()

if __name__ == '__main__':
    cfg = kts46.utils.getConfiguration()
    kts46.utils.configureLogging(cfg)
    logger = logging.getLogger(cfg.get('loggers', 'RPCServer'))

    # Create and configure server.
    address = cfg.get('rpc-server', 'bind-address')
    port = cfg.getint('rpc-server', 'port')
    try:
        rpcserver = SimpleXMLRPCServer((address, port), allow_none=True)
    except socket.error:
        logger.fatal("Couldn't bind to specified IP address: {0}.".format(address))
        sys.exit(1)

    # Check whether RPC server is actually enabled in this instance.
    if cfg.getboolean('servers', 'rpc-server'):
        logger.info('RPC server is enabled.')
        server = RPCServer(cfg)
        rpcserver.register_instance(server)
    else:
        logger.info('RPC server is disabled, but will be started as a dummy.')

    # Check whether worker is enabled in this instance.
    if cfg.getboolean('servers', 'worker'):
        logger.info('Worker is enabled.')
        p = Process(target=startWorker, args=(cfg,))
        p.start()
    else:
        logger.info('Worker is disabled.')

    # Run server.
    logger.info('Starting RPC server...')
    rpcserver.serve_forever()
