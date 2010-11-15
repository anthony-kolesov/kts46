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

import sys, Queue, couchdb, logging
from multiprocessing.managers import BaseManager
from ConfigParser import SafeConfigParser

sys.path.append('../lib/')
from kts46.serverApi import RPCServerException
from kts46 import CouchDBStorage, Model

class Scheduler(BaseManager):
    pass

class ModelParams:

    def __init__(self):
        self.carGenerationInterval = 3.0
        self.safeDistance = 5.0
        self.maxSpeed = 20.0
        self.minSpeed = 10.0

Scheduler.register('getJob')
Scheduler.register('runJob')
m = Scheduler(address=('localhost', 46211), authkey='anthony')
m.connect()

d = m.getJob()
#help(d)
#print(d.keys())
#print(d.values())
#print(d.items())
projectName = d.get('p')
jobName = d.get('j')

configFiles = ('../config/common.ini', '../config/rpc_server.ini')
cfg = SafeConfigParser()
cfg.read(configFiles)

logging.basicConfig(level=logging.INFO, format=cfg.get('log', 'format'),
                datefmt=cfg.get('log', 'dateFormat'))
logger = logging.getLogger('kts46.worker')
logger.info('I have a job: %s.%s' % (projectName, jobName))

server = couchdb.Server(cfg.get('couchdb', 'dbaddress'))
jobsListView = 'manage/jobs'

if projectName not in server:
    raise RPCServerException("Project '%s' doesn't exist." % projectName)
db = server[projectName]

# Use only first job. There acually can be only one.
jobsViewResult = db.view(jobsListView)[jobName]
jobIdStr = list(jobsViewResult)[0]['value'][1:]
jobId = int(jobIdStr)

# Prepare infrastructure.
storage = CouchDBStorage(cfg.get('couchdb', 'dbaddress'), projectName, str(jobId))

model = Model(ModelParams())
job = server[projectName]['j'+str(jobId)]
model.loadYAML(job['yaml'])
step = job['simulationStep']
duration = job['simulationTime']

# Prepare values.
stepAsMs = step * 1000 # step in milliseconds
stepsN = duration / step
stepsCount = 0
t = 0.0
logger.info('stepsN: %i, stepsCount: %i, stepsN/100: %i', stepsN, stepsCount, stepsN / 100)

# Run.
while t < duration:
    model.run_step(stepAsMs)
    stepsCount += 1
    # Round time to milliseconds
    data = model.get_state_data()
    data['job'] = jobId
    storage.add(round(t, 3), data)
    t += step

# Finilize.
storage.close()
