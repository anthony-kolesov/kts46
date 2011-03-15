# Copyright 2010-2011 Anthony Kolesov
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import threading
import time
import uuid
import socket
from socket import error as SocketException

import kts46
import kts46.utils
import kts46.rpcClient
import jsonRpcClient
from kts46.simulationServer import SimulationServer
from kts46.statisticsServer import StatisticsServer
from kts46.mongodb import Storage, StateStorage

def _notificationThreadImplementation(worker):
    while True:
        worker.enableNotificationEvent.wait()
        time.sleep(worker.notificationSleepTimeout)

        # Acquire lock here so worker will not remove it after condition test.
        worker.lastUpdateLock.acquire()
        # Event may have been disabled while we were waiting, so check here again.
        if worker.enableNotificationEvent.is_set():
            worker.log.debug('[%s] Sending notification to server...', threading.currentThread().name)
            try:
                #lu = worker.server.reportStatus(worker.workerId, 'working', worker.lastUpdate)
                sig = worker.server.taskInProgress(worker.workerId, worker.sig)['sig']
            except SocketException, msg:
                # Continue to work even if connection failed. Hope that next
                # time will be successful.
                worker.log.warning("Connection to RPC server failed. Couldn't notify server about task status. Continue to work.")
            worker.sig = sig
        worker.lastUpdateLock.release()


class WorkerException(Exception): pass

class Worker:

    def __init__(self, cfg, workerId=None):
        self.cfg = cfg
        self.log = logging.getLogger(cfg.get('loggers', 'Worker'))

        # Setup worker id. It must be unique in a workers network.
        if workerId is not None:
            self.workerId = workerId
        elif cfg.has_option('worker', 'id'):
            self.workerId = cfg.get('worker', 'id')
        else:
            self.workerId = str(uuid.uuid4())

        self.enableNotificationEvent = threading.Event()
        self.lastUpdateLock = threading.Lock()
        # Take default timeout from scheduler configuration.
        self.notificationSleepTimeout = cfg.getint('scheduler', 'notifyInterval')

        # Create server proxy.
        self.server = kts46.rpcClient.getJsonRpcClient(cfg)
        self.startNotificationThread()

        # Create db storage.
        self.storage = None
        #self.storage = Storage(self.cfg.get('mongodb', 'host'))

        # Get possible task types.
        self.possibleTypes = map(str.strip, cfg.get("worker", "possibleTasks").split(","))

    def run(self):
        "Runs a worker loop."

        # Start run loop.
        while True:
            # Try to get a task.
            try:
                taskTypes = self.possibleTypes
                task = self.server.getTask(self.workerId, taskTypes)
            except SocketException, msg:
                self.log.error("Couldn't connect to RPC server. Message: %s", msg)
                task = {'empty': True}

            # Sleep if there is nothing to do.
            if task['empty']:
                sleepTime = self.cfg.getfloat('worker', 'checkInterval')
                self.log.debug('Worker has nothing to do. Sleeping for %f s.', sleepTime)
                time.sleep(sleepTime) # Wait some time for new job.
                continue

            # There is a task.
            projectName = task['project']
            jobName = task['job']
            # Report status isn't enabled at this time, so no need to lock.
            self.sig = task['sig']

            # Create storage
            dbHost = task['databases'][0]['host']
            dbPort = task['databases'][0]['port']
            if (self.storage is None or self.storage.host != dbHost or
                    self.storage.port != dbPort):
                self.storage = Storage(dbHost, dbPort)

            try:
                self.log.debug("Accepting task")
                self.sig = self.server.acceptTask(self.workerId, self.sig)['sig']
            except jsonRpcClient.RPCException as ex:
                self.log.error("Couldn't accept task from server: %s", str(ex))
                time.sleep(sleepTime) # Wait some time for new job.
                continue

            # interval is provided in milliseconds
            self.notificationSleepTimeout = task['notificationInterval'] / 1000
            self.enableNotificationEvent.set() # Start notifying scheduler about our state.
            job = self.getJob(projectName, jobName)

            if task['type'] == 'simulation':
                self.log.info('Starting simulation task: {0}.{1} [{2}/{3}].'.format(
                    projectName, jobName, job.progress['done'], job.progress['totalSteps']))
                simServer = SimulationServer(self.cfg)
                stateStorage = StateStorage(job, self.cfg.getint('worker', 'dbBatchLength'));
                simServer.runSimulationJob(job, stateStorage)
            elif task['type'] == 'basicStatistics':
                self.log.info('Starting basicStatistics task: {0}.{1}.'.format(projectName, jobName))
                stServer = StatisticsServer(self.cfg)
                stServer.calculateBasicStats(job)
            elif task['type'] == 'idleTimes':
                self.log.info('Starting idleTimes statistics task: {0}.{1}.'.format(projectName, jobName))
                stServer = StatisticsServer(self.cfg)
                stServer.calculateIdleTimes(job)
            elif task['type'] == 'throughput':
                self.log.info('Starting throughput statistics task: {0}.{1}.'.format(projectName, jobName))
                stServer = StatisticsServer(self.cfg)
                stServer.calculateThroughput(job)

            statistics = kts46.utils.getMemoryUsage()
            statistics['hostName'] = socket.gethostname()
            statistics['version'] = kts46.__version__

            # Notify server.
            # Lock here so if condition in sync thread will be correct.
            self.lastUpdateLock.acquire()
            self.enableNotificationEvent.clear() # Stop notifying scheduler.
            finishedSent = False
            while not finishedSent:
                try:
                    #self.server.reportStatus(self.workerId, 'finished', self.lastUpdate)
                    self.server.taskFinished(self.workerId, self.sig, statistics)
                    finishedSent = True
                except SocketException, msg:
                    self.log.error("Connection to RPC server failed. Waiting for it.")
                    time.sleep(self.cfg.getfloat('worker', 'checkInterval'))
                except jsonRpcClient.RPCException as ex:
                    self.log.error("Error negotiating with RPC server: %s.", str(ex))
                    finishedSent = True # Couldn't recover from this error.
            self.lastUpdateLock.release()


    def startNotificationThread(self):
        "Starts thread to notify scheduler about worker availability and returns Thread object."
        t = threading.Thread(target=_notificationThreadImplementation, kwargs={'worker':self})
        t.daemon = True
        t.start()
        return t


    def getJob(self, projectName, jobName):
        if projectName not in self.storage:
            raise WorkerException("Project '{0}' doesn't exist.".format(projectName))
        project = self.storage[projectName]

        if jobName not in project:
            msg = "Job with name '{0}' doesn't exist in project '{1}'."
            raise WorkerException(msg.format(jobName, projectName))
        return project[jobName]
