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


import sys # for sys.exc_info()
import logging
import traceback
from kts46.server.database import DatabaseServer
from kts46.server.scheduler import SchedulerServer
from kts46.server.status import StatusServer


class RPCServer:
    # Currently all subservers are used by delegating calls to them.

    def __init__(self, cfg):
        self._scheduler = SchedulerServer(cfg)
        self._db = DatabaseServer(cfg)
        self._status = StatusServer(cfg)
        self._log = logging.getLogger(cfg.get('loggers', 'RPCServer'))

    def hello(self):
        "Test method to check that server is working fine."
        self._log.info('Method: hello')
        msg = "Hello you too! This is XML-RPC server for kts46."
        return msg

    # Scheduler functions.
    def runJob(self, projectName, jobName):
       self._log.info('Method: runJob %s %s', projectName, jobName)
       self._scheduler.runJob(projectName, jobName)

    def getJob(self, workerId):
       self._log.info('Method: getJob %s', workerId)
       return self._scheduler.getJob(workerId)

    def reportStatus(self, workerId, state, lastUpdate):
       self._log.info('Method: reportStatus %s %s %s', workerId, state, lastUpdate)
       return self._scheduler.reportStatus(workerId, state, lastUpdate)

    def getCurrentTasks(self):
       self._log.info('Method: getCurrentTasks')
       return self._scheduler.getCurrentTasks()

    def restartTask(self, workerId, lastUpdate):
       self._log.info('Method: restartTask %s %s', workerId, lastUpdate)
       return self._scheduler.restartTask(workerId, lastUpdate)

    # Database functions.
    def getNewJobId(self, projectName):
        self._log.info('Method: getNewJobId %s', projectName)
        return self._db.getNewJobId(projectName)

    def createProject(self, projectName):
        self._log.info('Method: createProject %s', projectName)
        self._db.createProject(projectName)

    def projectExists(self, projectName):
        self._log.info('Method: projectExists %s', projectName)
        return self._db.projectExists(projectName)

    def deleteProject(self, projectName):
        self._log.info('Method: deleteProject %s', projectName)
        self._db.deleteProject(projectName)

    def addJob(self, projectName, jobName, definition):
        self._log.info('Method: addJob %s %s ...', projectName, jobName)
        try:
            self._db.addJob(projectName, jobName, definition)
        except NameError as ex:
            self._log.error("Couldn't add job: %s", ex)
            traceback.print_exc()
            raise

    def jobExists(self, projectName, jobName):
        self._log.info('Method: jobExists %s %s', projectName, jobName)
        return self._db.jobExists(projectName, jobName)

    def deleteJob(self, projectName, jobName):
        self._log.info('Method: deleteJob %s %s', projectName, jobName)
        self._db.deleteJob(projectName, jobName)

    def getJobStatus(self, project, job):
        self._log.info('Method: getJobStatus %s %s', project, job)
        return self._status.getJobStatus(project, job)

    def getJobsList(self, project):
        self._log.info('Method: getJobsList %s', project)
        return self._status.getJobsList(project)

    def getProjectStatus(self, project):
        self._log.info('Method: getProjectStatus %s', project)
        return self._status.getProjectStatus(project)

    def getServerStatus(self):
        self._log.debug('Method: getServerStatus')
        try:
            return self._status.getServerStatus()
        except AttributeError as ex:
            self._log.error('Method `getServerStatus`: ' + str(ex))
            return []

    def getJobStatistics(self, project, job, includeIdleTimes):
        self._log.debug("Method getJobStatistics %s %s", project, job)
        try:
            return self._status.getJobStatistics(project, job, includeIdleTimes)
        except KeyError:
            self._log.error("getJobStatistics: invalid project or job name: %s, %s.", project, job)
            return { }

    def getModelDescription(self, project, job):
        return self._status.getModelDescription(project, job)
        
    def getModelState(self, project, job, time):
        return self._status.getModelState(project, job, time)