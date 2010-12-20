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

def getScheduler(cfg):
    # Create RPC proxy.
    host = cfg.get('worker', 'server')
    port = cfg.getint('rpc-server', 'port')
    connString = 'http://%s:%i' % (host, port)
    proxy = xmlrpclib.ServerProxy(connString)
    return proxy

def getJob(storage, projectName, jobName):
    if projectName not in storage:
        raise RPCServerException("Project '%s' doesn't exist." % projectName)
    project = storage[projectName]

    if jobName not in project:
        raise RPCServerException("Job with name '{0}' doesn't exist in project '{1}'.".format(
            jobName, projectName))
    return project[jobName]


def notificationThreadImplementation(scheduler, workerId, enableEvent):
    while True:
        enableEvent.wait()
        time.sleep(g_notificationSleepTimeout)
        # Event may have been disabled while we were waiting, so check here again.
        if enableEvent.is_set():
            logger.info('[%s] Sending notification to server...', threading.currentThread().name)
            scheduler.reportStatus(workerId, 'working')


def startNotificationThread(scheduler, workerId, enableEvent):
    "Starts thread to notify scheduler about worker availability and returns Thread object."
    t = threading.Thread(target=notificationThreadImplementation, kwargs={
        'scheduler':scheduler, 'workerId':workerId, 'enableEvent':enableEvent })
    t.daemon = True
    t.start()
    return t


# Init app infrastructure
cmdOpts = OptionParser()
cmdOpts.add_option('-i', '--id', action='store', dest='id', default='',
                       help='Worker id. Must be unique in a network of workers.')
options, args = cmdOpts.parse_args(sys.argv[1:])


cfg = kts46.utils.getConfiguration(('../config/worker.ini',))
logger = kts46.utils.getLogger(cfg)
if len(options.id) > 0:
    workerId = options.id # 'worker-1'
elif cfg.has_option('worker', 'id'):
    workerId = cfg.get('worker', 'id')
else:
    workerId = str(uuid.uuid4())

enableNotificationEvent = threading.Event()
g_notificationSleepTimeout = 5

# Create scheduler.
m = getScheduler(cfg)
startNotificationThread(scheduler=m, workerId=workerId,
                        enableEvent=enableNotificationEvent)
#startNotificationThread(interval=task.get('timeout'), scheduler=m, workerId=workerId)

# Start run loop.
while True:
    task = m.getJob(workerId)
    # task is a AutoProxy, not None. So we coudn't check for `is None`. May be there
    # is a better way than comparing strings but that works.
    if str(task) == "None":
        logger.warning('Oops. Nothing to do.')
        time.sleep(cfg.getfloat('worker', 'checkTimeout')) # Wait some time for job.
        continue
    projectName = task.get('project')
    jobName = task.get('job')
    initialStateId = task.get('stateId')
    logger.info('I have a task: %s.%s', projectName, jobName)
    g_notificationSleepTimeout = task.get('timeout')

    enableNotificationEvent.set() # Start notifying scheduler about our state.
    storage = kts46.CouchDBStorage.CouchDBStorage(cfg.get('couchdb', 'dbaddress'))
    job = getJob(storage, projectName, jobName)

    simServer = SimulationServer()
    simServer.runSimulationJob(job)

    # Notify server.
    enableNotificationEvent.clear() # Stop notifying scheduler.
    m.reportStatus(workerId, 'finished')
