#!/usr/bin/python
"""
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

import sys, uuid, datetime, xmlrpclib
import time, threading # For daemon thread that will send notification to scheduler.
from optparse import OptionParser

sys.path.append('../lib/')
import kts46.utils
import kts46.CouchDBStorage
import kts46.schedulerClient
from kts46.serverApi import RPCServerException
from kts46.simulationServer import SimulationServer
from kts46.statisticsServer import StatisticsServer
from kts46.server.worker import Worker

# Init app infrastructure
cmdOpts = OptionParser()
cmdOpts.add_option('-i', '--id', action='store', dest='id', default='',
                       help='Worker id. Must be unique in a network of workers.')
options, args = cmdOpts.parse_args(sys.argv[1:])


cfg = kts46.utils.getConfiguration(('../config/worker.ini',))
kts46.utils.configureLogging(cfg)
if len(options.id) > 0:
    workerId = options.id # 'worker-1'
else:
    workerId = None

w = Worker(cfg, workerId)
w.run()
