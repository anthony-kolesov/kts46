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

import sys, Queue, couchdb, logging, uuid, yaml, datetime
import time, threading # For daemon thread that will send notification to scheduler.
from multiprocessing.managers import SyncManager
from ConfigParser import SafeConfigParser

sys.path.append('../lib/')
import kts46.utils
from kts46.serverApi import RPCServerException
from kts46 import Model
import kts46.CouchDBStorage

def timedeltaToSeconds(td):
    return td.days * 24 * 60 * 60 + td.seconds + td.microseconds / 1000000.0

def getScheduler(cfg):
    # Create scheduler.
    Scheduler.register('getJob')
    Scheduler.register('runJob')
    Scheduler.register('reportStatus')
    schedulerAddress = (cfg.get('scheduler', 'address'), cfg.getint('scheduler', 'port'))
    schedulerAuthkey = cfg.get('scheduler', 'authkey')
    m = Scheduler(address=schedulerAddress, authkey=schedulerAuthkey)
    m.connect()
    return m


def getJob(storage, projectName, jobName):
    if projectName not in storage:
        raise RPCServerException("Project '%s' doesn't exist." % projectName)
    project = storage[projectName]

    if jobName not in project:
        raise RPCServerException("Job with name '{0}' doesn't exist in project '{1}'.".format(
            jobName, projectName))
    return project[jobName]


def notificationThreadImplementation(interval, scheduler, workerId):
    while True:
        g_enableNotificationEvent.wait()
        time.sleep(interval)
        # Event may have been disabled while we were waiting, so check here again.
        if g_enableNotificationEvent.is_set():
            logger.info('[%s] Sending notification to server...', threading.currentThread().name)
            scheduler.reportStatus(workerId, 'working')


def startNotificationThread(interval, scheduler, workerId):
    "Starts thread to notify scheduler about worker availability and returns Thread object."
    t = threading.Thread(target=notificationThreadImplementation, kwargs={
                        'interval': interval, 'scheduler':scheduler, 'workerId':workerId})
    t.daemon = True
    t.start()
    return t


def runSimulationJob(job):
    """Runs simulation job.

    This function does all required stuff: gets initial state and definition,
    simulates and stores simulation results to database."""

    jobId = job.id

    model = Model(ModelParams())
    model.loadYAML(job.definition)
    step = job.simulationParameters['stepDuration']
    duration = job.simulationParameters['duration']
    batchLength = job.simulationParameters['batchLength']


    # Prepare infrastructure.
    saver = kts46.CouchDBStorage.CouchDBStateStorage(job, model.asYAML)

    # Load current state: load state and set time
    if len(job.progress['currentFullState']) > 0:
        model.loadYAML(job.progress['currentFullState'])
        t = timedeltaToSeconds(model.time)
    else:
        t = 0.0

    # Reset job progres step counter.
    if t == 0.0:
        # Document will be saved to database with state data.
        job.progress['done'] = 0

    # Prepare values.
    stepAsMs = step * 1000 # step in milliseconds
    stepsN = job.simulationParameters['duration'] / step
    stepsCount = 0
    # t = 0.0
    logger.info('stepsN: %i, stepsCount: %i, stepsN/100: %i', stepsN, stepsCount, stepsN / 100)


    # Run.
    while t <= duration and stepsCount < batchLength:
        model.run_step(stepAsMs)
        stepsCount += 1
        data = model.get_state_data()
        data['job'] = jobId
        # Round time to milliseconds
        saver.add(round(t, 3), data)
        t += step
        time.sleep(1)

    # Finilize.
    saver.close()

    #f1 = open('/tmp/kts46-state.txt', 'w')
    #f1.write(model.asYAML())
    #f1.close()

class Scheduler(SyncManager):
    pass


class ModelParams:

    def __init__(self):
        self.carGenerationInterval = 3.0
        self.safeDistance = 5.0
        self.maxSpeed = 20.0
        self.minSpeed = 10.0


# Init app infrastructure
cfg = kts46.utils.getConfiguration(('../config/worker.ini',))
logger = kts46.utils.getLogger(cfg)
workerId = 'worker-1' # uuid.uuid4()
g_enableNotificationEvent = threading.Event()

# Create scheduler.
m = getScheduler(cfg)
startNotificationThread(interval=5, scheduler=m, workerId=workerId)
#startNotificationThread(interval=task.get('timeout'), scheduler=m, workerId=workerId)

# Start run loop.
while True:
    task = m.getJob(workerId)
    # task is a AutoProxy, not None. So we coudn't check for `is None`. May be there
    # is a better way than comparing strings but that works.
    if str(task) == "None":
        logger.warning('Oops. Nothing to do.')
        time.sleep(5) # Wait some time for job.
        continue # sys.exit(0)
    projectName = task.get('project')
    jobName = task.get('job')
    initialStateId = task.get('stateId')
    logger.info('I have a task: %s.%s', projectName, jobName)


    g_enableNotificationEvent.set() # Start notifying scheduler about our state.

    storage = kts46.CouchDBStorage.CouchDBStorage(cfg.get('couchdb', 'dbaddress'))


    job = getJob(storage, projectName, jobName)

    runSimulationJob(job)

    # Notify server.
    g_enableNotificationEvent.clear() # Stop notifying scheduler.
    m.reportStatus(workerId, 'finished')
