"""
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

import threading, time, logging, uuid, xmlrpclib
from xmlrpclib import ServerProxy
from socket import error as SocketException
import kts46.utils
from kts46.serverApi import RPCServerException
from kts46.CouchDBStorage import CouchDBStorage
from kts46.simulationServer import SimulationServer
from kts46.statisticsServer import StatisticsServer

def _notificationThreadImplementation(worker):
    while True:
        worker.enableNotificationEvent.wait()
        time.sleep(worker.notificationSleepTimeout)

        # Acquire lock here so worker will not remove it after condition test.
        worker.lastUpdateLock.acquire()
        # Event may have been disabled while we were waiting, so check here again.
        if worker.enableNotificationEvent.is_set():
            worker.log.info('[%s] Sending notification to server...', threading.currentThread().name)
            try:
                lu = worker.server.reportStatus(worker.workerId, 'working', worker.lastUpdate)
            except SocketException, msg:
                # Continue to work even if connection failed. Hope that next
                # time will be successful.
                worker.log.warning("Connection to RPC server failed. Couldn't notify server about task status. Continue to work.")
            worker.lastUpdate = lu
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
        self.server = kts46.utils.getRPCServerProxy(cfg)
        self.startNotificationThread()

        # Create db storage.
        self.storage = CouchDBStorage(self.cfg.get('couchdb', 'dbaddress'))


    def run(self):
        "Runs a worker loop."

        # Start run loop.
        while True:
            # Try to get a task.
            try:
                task = self.server.getJob(self.workerId)
            except SocketException, msg:
                self.log.error("Couldn't connect to RPC server. Message: %s", msg)
                task = None

            # Sleep if there is nothing to do.
            # task is a AutoProxy, not None. So we coudn't check for `is None`. May be there
            # is a better way than comparing strings but that works.
            if str(task) == "None":
                sleepTime = self.cfg.getfloat('worker', 'checkInterval')
                self.log.debug('Worker has nothing to do. Sleeping for %f s.', sleepTime)
                time.sleep(sleepTime) # Wait some time for new job.
                continue

            # There is a task.
            projectName = task.get('project')
            jobName = task.get('job')
            # Report status isn't enabled at this time, so no need to lock.
            self.lastUpdate = task.get('lastUpdate')

            self.notificationSleepTimeout = task.get('timeout')
            self.enableNotificationEvent.set() # Start notifying scheduler about our state.
            job = self.getJob(projectName, jobName)

            if task.get('type') == 'simulation':
                self.log.info('Starting simulation task: {0}.{1}.'.format(projectName, jobName))
                simServer = SimulationServer()
                simServer.runSimulationJob(job)
            elif task.get('type') == 'statistics':
                self.log.info('Starting statistics task: {0}.{1}.'.format(projectName, jobName))
                stServer = StatisticsServer(self.cfg)
                stServer.calculate(projectName, job)

            # Notify server.
            # Lock here so if condition in sync thread will be correct.
            self.lastUpdateLock.acquire()
            self.enableNotificationEvent.clear() # Stop notifying scheduler.
            finishedSent = False
            while not finishedSent:
                try:
                    self.server.reportStatus(self.workerId, 'finished', self.lastUpdate)
                    finishedSent = True
                except SocketException, msg:
                    self.log.error("Connection to RPC server failed. Waiting for it.")
                    time.sleep(self.cfg.getfloat('worker', 'checkInterval'))
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
