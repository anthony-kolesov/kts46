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

import Queue, threading, logging, logging.handlers
from multiprocessing.managers import BaseManager
from ConfigParser import SafeConfigParser


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


unstartedJobs = Queue.Queue()
currentJobs = Queue.Queue()
cfg = createConfiguration()
logger = createLogger()


class Scheduler(BaseManager): pass


def runJob(projectName, jobName):
    logger.info('Adding job: project=%s, job=%s' % (projectName, jobName))
    unstartedJobs.put({'p':projectName, 'j':jobName})


def getJob():
    a = unstartedJobs.get()
    logger.info('Removing from queue: project=%s, job=%s' % (a['p'], a['j']))
    return a

if __name__ == '__main__':
    logger.info('Starting scheduler.')
    Scheduler.register('runJob', callable=runJob)
    Scheduler.register('getJob', callable=getJob)

    manager = Scheduler(address=('', cfg.getint('scheduler', 'port')),
                        authkey=cfg.get('scheduler', 'authkey') )

    logger.info('Scheduler is starting to serve.')
    server = manager.get_server()
    server.serve_forever()
