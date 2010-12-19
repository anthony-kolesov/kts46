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

import sys
#import Queue, threading, logging, logging.handlers, time
from multiprocessing import Queue, Manager
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
        self._log = kts46.utils.getLogger(configuration)
        self.storage = CouchDBStorage(configuration.get('couchdb', 'dbaddress'))
        self.timeout = configuration.getint('scheduler', 'timeout')
        # Task statuses.
        self.stateNameWorking = configuration.get('scheduler', 'workingStateName')
        self.stateNameAbort= configuration.get('scheduler', 'abortStateName')
        self.stateNameFinished = configuration.get('scheduler', 'finishedStateName')

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
            return

        self._log.info('Adding new job part: [project=%s, job=%s, progress:%i/%i]',
            projectName, jobName, job.progress['done'], job.progress['totalSteps'])
        d = {'project':projectName, 'job':jobName,
             'timeout': self.timeout}
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
        if state == WORKING_STATE_NAME:
            self._log.info('Task is still in progress: {0}.{1}, worker={2}'.format(
                task['project'], task['job'], workerId) )
            taskInfo['lastUpdate'] = datetime.utcnow()
        elif state == ABORT_STATE_NAME:
            self._log.info('Aborting task: {0}.{1}.'.format(task['project'], task['job']))
            del self._currentTasks[workerId]
            self._waitingTasks.task_done()
            self._waitingTasks.append(task)
        elif state == FINISHED_STATE_NAME:
            self._log.info('Task is finished: {0}.{1}.'.format(task['project'], task['job']))
            del self._currentTasks[workerId]
            self._waitingTasks.task_done()
            self.runJob(task['project'], task['job'])
