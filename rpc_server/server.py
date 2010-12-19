#!/usr/bin/python
"""
Description:
    Runs all kts46 server processes.

License:
   Copyright 2010 Anthony Kolesov

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

import logging, logging.handlers, sys
from ConfigParser import SafeConfigParser
from multiprocessing.managers import SyncManager
from SimpleXMLRPCServer import SimpleXMLRPCServer
# Project imports
PROJECT_LIB_PATH = '../lib/'
if PROJECT_LIB_PATH not in sys.path:
    sys.path.append(PROJECT_LIB_PATH)
import kts46.utils
from kts46.server.scheduler import SchedulerServer

__version__ = "0.1.2"

class Server:
    # Currently all subservers are used by delegating calls to them.

    def __init__(self, cfg):
        self._scheduler = SchedulerServer(cfg)

    def hello(self):
        "Test method to check that server is working fine."
        msg = "Hello you too! This is XML-RPC server for kts46. Version: {0}."
        msg = msg.format(__version__)
        return msg

    def runJob(self, projectName, jobName):
        self._scheduler.runJob(projectName, jobName)

    def getJob(self, workerId):
        return self._scheduler.getJob(workerId)

    def reportStatus(self, workerId, state):
        self._scheduler.reportStatus(workerId, state)


if __name__ == '__main__':
    cfg = kts46.utils.getConfiguration(('../config/server.ini',))
    logger = kts46.utils.getLogger(cfg)

    # Create and configure server.
    address = cfg.get('rpc-server', 'address')
    port = cfg.getint('rpc-server', 'port')
    rpcserver = SimpleXMLRPCServer( (address, port), allow_none = True )

    # Register functions.
    server = Server(cfg)
    rpcserver.register_instance(server)

    # Run server.
    logger.info('Starting RPC server...')
    rpcserver.serve_forever()
