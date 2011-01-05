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
from time import sleep
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


def startRPCServer(cfg, log):
    logger.info('RPC server is enabled.')

    # Create and configure server.
    address = cfg.get('rpc-server', 'bind-address')
    port = cfg.getint('rpc-server', 'port')
    try:
        rpcserver = SimpleXMLRPCServer((address, port), allow_none=True)
    except socket.error:
        log.fatal("Couldn't bind to specified IP address: {0}.".format(address))
        sys.exit(1)

    server = RPCServer(cfg)
    rpcserver.register_instance(server)
    # Run server.
    log.info('Starting RPC server...')
    rpcserver.serve_forever()

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
    logger = logging.getLogger(cfg.get('loggers', 'Node'))
    options, args = configureCmdOptions()

    rpcProcess, workerProcess = (None, None)
    supervisorProcess, httpProcess = (None, None)
    checkInterval = cfg.getfloat('node', 'deadChildCheckInterval')

    while True:
        if 'rpc-server' in args:
            if rpcProcess is None or not rpcProcess.is_alive():
                logger.info("Starting RPC server process.")
                rpcProcess = Process(target=startRPCServer, args=(cfg, logger))
                rpcProcess.start()
        if 'worker' in args:
            if workerProcess is None or not workerProcess.is_alive():
                logger.info("Starting worker process.")
                workerProcess = Process(target=startWorker, args=(cfg, options.wid))
                workerProcess.start()
        if 'http' in args:
            if httpProcess is None or not httpProcess.is_alive():
                logger.info("Starting http process.")
                httpProcess = Process(target=startHTTPServer, args=(cfg,))
                httpProcess.start()
        if 'supervisor' in args:
            if supervisorProcess is None or not supervisorProcess.is_alive():
                logger.info("Starting supervisor process.")
                supervisorProcess = Process(target=startSupervisor, args=(cfg,))
                supervisorProcess.start()
        sleep(checkInterval)
