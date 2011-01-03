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

from kts46.server.scheduler import SchedulerServer
from kts46.server.database import DatabaseServer
from kts46.server.status import StatusServer


class RPCServer:
    # Currently all subservers are used by delegating calls to them.

    def __init__(self, cfg):
        self._scheduler = SchedulerServer(cfg)
        self._db = DatabaseServer(cfg)
        self._status = StatusServer(cfg)

    def hello(self):
        "Test method to check that server is working fine."
        msg = "Hello you too! This is XML-RPC server for kts46."
        return msg

    # Scheduler functions.
    def runJob(self, projectName, jobName):
        self._scheduler.runJob(projectName, jobName)

    def getJob(self, workerId):
        return self._scheduler.getJob(workerId)

    def reportStatus(self, workerId, state):
        self._scheduler.reportStatus(workerId, state)

    def getCurrentTasks(self): return self._scheduler.getCurrentTasks()

    def restartTask(self, workerId, lastUpdate):
        return self._scheduler.restartTask(workerId, lastUpdate)

    # Database functions.
    def getNewJobId(self, projectName):
        return self._db.getNewJobId(projectName)

    def createProject(self, projectName):
        self._db.createProject(projectName)

    def projectExists(self, projectName):
        return self._db.projectExists(projectName)

    def deleteProject(self, projectName):
        self._db.deleteProject(projectName)

    def addJob(self, projectName, jobName, definition):
        self._db.addJob(projectName, jobName, definition)

    def jobExists(self, projectName, jobName):
        return self._db.jobExists(projectName, jobName)

    def deleteJob(self, projectName, jobName):
        self._db.deleteJob(projectName, jobName)

    def getJobStatus(self, project, job): return self._status.getJobStatus(project, job)
    def getJobsList(self, project): return self._status.getJobsList(project)
    def getProjectStatus(self, project): return self._status.getProjectStatus(project)
    def getServerStatus(self): return self._status.getServerStatus()
