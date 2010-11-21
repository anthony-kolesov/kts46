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

import Queue, threading, logging, logging.handlers, sys
from multiprocessing.managers import SyncManager
from ConfigParser import SafeConfigParser
from datetime import datetime

sys.path.append('../lib/')
from kts46.CouchDBStorage import CouchDBStorage


def createConfiguration():
    "Returns SafeConfigParser for this application."
    configFiles = ('../config/common.ini', '../config/scheduler.ini')
    cfg = SafeConfigParser()
    cfg.read(configFiles)
    return cfg

def createLogger():
    logging.getLogger('').setLevel(logging.INFO)
    logging.basicConfig(format=cfg.get('log', 'format'))

    # Define a log handler for rotating files.
    rfhandler = logging.handlers.RotatingFileHandler(cfg.get('log', 'filename'),
        maxBytes=cfg.get('log', 'maxBytesInFile'),
        backupCount=cfg.get('log', 'backupCountOfFile'))
    rfhandler.setLevel(logging.INFO)
    rfhandler.setFormatter(logging.Formatter(cfg.get('log', 'format')))
    logging.getLogger('').addHandler(rfhandler)

    logger = logging.getLogger(cfg.get('log', 'loggerName'))
    logger.setLevel(logging.INFO)
    return logger

cfg = createConfiguration()
logger = createLogger()
storage = CouchDBStorage(cfg.get('couchdb', 'dbaddress'))
WORKING_STATE_NAME = cfg.get('scheduler', 'workingStateName')
ABORT_STATE_NAME = cfg.get('scheduler', 'abortStateName')
FINISHED_STATE_NAME = cfg.get('scheduler', 'finishedStateName')

class Scheduler(SyncManager): pass


def runJob(projectName, jobName, restart=False):
    """Starts or continues simulation job.

    To avoid multiple creation of project/job objects and extra communication
    with DB server check for whether this job is finished is done here. So
    simulated job won't start. If user wants to restart simulation job than
    he/she must explicitly set `restart` parameter to True."""

    #if currentTasks == 0:
    #    logger.info('Creating currentTasks list.')
    #    currentTasks = manager.dict()

    job = storage[projectName][jobName]
    lastStateId = job.progress['currentStateId']
    if restart:
        lastStateId = ''

    logger.info('Adding new job part: [project=%s, job=%s, currentState=%s]',
                projectName, jobName, lastStateId)
    d = {'project':projectName, 'job':jobName, 'stateId': lastStateId,
         'timeout': cfg.getint('scheduler', 'timeout') }
    waitingTasks.put(d)


#def runJob(projectName, jobName):
#    logger.info('Adding job: project=%s, job=%s' % (projectName, jobName))
#    d = {'project':projectName, 'job':jobName, 'stateId': '',
#         'timeout': cfg.getint('scheduler', 'timeout') }
#    waitingTasks.put(d)


def getJob(workerId):
    try:
        task = waitingTasks.get_nowait()
    except Queue.Empty:
        return None

    logger.info('Starting task: project={0}, job={1}'.format(task['project'], task['job']))
    currentTasks[workerId] = {'task': task, 'lastUpdate': datetime.utcnow()}
    return task


def reportStatus(workerId, state):
    taskInfo = currentTasks[workerId]
    if state == WORKING_STATE_NAME:
        taskInfo['lastUpdate'] = datetime.utcnow()
    elif state == ABORT_STATE_NAME:
        task = taskInfo['task']
        del currentTasks[workerId]
        waitingTasks.append(task)
    elif state == FINISHED_STATE_NAME:
        del currentTasks[workerId]
        task = taskInfo['task']
        runJob(task['project'], task['job'])


if __name__ == '__main__':
    logger.info('Starting scheduler.')
    Scheduler.register('runJob', callable=runJob)
    Scheduler.register('getJob', callable=getJob)
    Scheduler.register('reportStatus', callable=reportStatus)

    manager = Scheduler(address=('', cfg.getint('scheduler', 'port')),
                        authkey=cfg.get('scheduler', 'authkey') )

    waitingTasks = Queue.Queue()
    #currentTasks = 0

    logger.info('Scheduler is starting to serve.')
    #server = manager.get_server()
    #server.serve_forever()
    manager.start()
    logger.info('Creating currentTasks list.')
    currentTasks = manager.dict() # Queue.Queue()
    sys.stdin.readline()
