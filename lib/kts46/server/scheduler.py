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

import sys, Queue, logging
from multiprocessing import Manager
from multiprocessing.managers import SyncManager
from datetime import datetime
# Project imports.
sys.path.append('../../../lib/')
import kts46.utils
from kts46.CouchDBStorage import CouchDBStorage


class SchedulerManager(SyncManager): pass


class SchedulerServer:

    def __init__(self, configuration):
        """Initializes new instance of SchedulerServer.

        Arguments:
          configuration - ConfigParser of application configuration."""
        self._cfg = configuration
        self._log = logging.getLogger(configuration.get('loggers', 'Scheduler'))
        self.storage = CouchDBStorage(configuration.get('couchdb', 'dbaddress'))
        self.timeout = configuration.getint('scheduler', 'timeout')
        # Task statuses.
        self.stateNameWorking = configuration.get('scheduler', 'workingStateName')
        self.stateNameAbort = configuration.get('scheduler', 'abortStateName')
        self.stateNameFinished = configuration.get('scheduler', 'finishedStateName')
        self.jobTypeSimulation = 'simulation'
        self.jobTypeStatistics = 'statistics'

        # Multithreaded items.
        self._manager = SchedulerManager()
        self._manager.start()
        self._waitingTasks = self._manager.Queue()
        self._currentTasks = self._manager.dict()


    def runJob(self, projectName, jobName):
        """Starts or continues simulation job.

        To avoid multiple creation of project/job objects and extra communication
        with DB server check for whether this job is finished is done here. So
        simulated job won't start."""

        job = self.storage[projectName][jobName]

        # Check whether simulation has been finished.
        if job.progress['done'] >= job.progress['totalSteps']:
            # Add statistics task.
            self.addStatisticsTask(projectName, jobName)
        else:
            self._log.info('Adding new job part: [project=%s, job=%s, progress:%i/%i]',
                projectName, jobName, job.progress['done'], job.progress['totalSteps'])
            d = {'project':projectName, 'job':jobName,
                 'timeout': self.timeout, 'type': self.jobTypeSimulation}
            self._waitingTasks.put(d)

    def addStatisticsTask(self, projectName, jobName):
        if self.storage[projectName][jobName].statistics['finished']:
            self._log.info('Statistics already calculated. Finish')
        else:
            self._log.info('Adding statistics task: project={0}, job={1}.'.format(
                projectName, jobName))
            d = {'project':projectName,
                'job':jobName,
                'timeout': self.timeout,
                'type': self.jobTypeStatistics}
            self._waitingTasks.put(d)


    def getJob(self, workerId):
        try:
            task = self._waitingTasks.get_nowait()
        except Queue.Empty:
            # If there is no task, than return None, so the worker will not be staled.
            return None

        self._log.info('Starting task: project={0}, job={1}'.format(task['project'], task['job']))
        self._currentTasks[workerId] = {'task': task, 'lastUpdate': datetime.utcnow()}
        return task


    def reportStatus(self, workerId, state):
        taskInfo = self._currentTasks[workerId]
        task = taskInfo['task']
        if state == self.stateNameWorking:
            self._log.info('Task is still in progress: {0}.{1}, worker={2}'.format(
                task['project'], task['job'], workerId))
            taskInfo['lastUpdate'] = datetime.utcnow()
        elif state == self.stateNameAbort:
            self._log.info('Aborting task: {0}.{1}.'.format(task['project'], task['job']))
            del self._currentTasks[workerId]
            self._waitingTasks.task_done()
            self._waitingTasks.append(task)
        elif state == self.stateNameFinished:
            self._log.info('Task is finished: {0}.{1}.'.format(task['project'], task['job']))
            del self._currentTasks[workerId]
            self._waitingTasks.task_done()
            self.runJob(task['project'], task['job'])

    def getCurrentTasks(self):
        """Gets status of current tasks. This function is used by supervisor to
        find staled tasks."""

        r = []
        for workerId in self._currentTasks.keys():
            task = self._currentTasks[workerId]
            info = {'workerId': workerId,
                    'lastUpdate': task['lastUpdate'],
                    'project': task['task']['project'],
                    'job': task['task']['job']}
            r.append(info)
        return r

    def restartTask(self, workerId, lastUpdate):
        if workerId not in self._currentTasks:
            msg = "Couldn't restart task because workerId `{wid}` is unknown."
            msg = msg.format(wid=workerId)
            self._log.error(msg)
            return False

        taskInfo = self._currentTasks[workerId]
        task = taskInfo['task']

        if taskInfo['lastUpdate'] != lastUpdate:
            msg = "Couldn't restart task `{p}.{j}` because `lastUpdate` is invalid."
            msg = msg.format(p=task['project'], j=task['job'])
            self._log.error(msg)
            return False

        # Report tasks as aborted and add it to queue again.
        self.reportStatus(workerId, self.stateNameAbort)
        self.runJob(task['project'], task['job'])
        return True
