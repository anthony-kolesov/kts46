# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2011 Anthony Kolesov
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import logging
import pymongo # connect with db
import yaml # parse model definition
import math # Math.floor


# Constants
JOBS_COUNT_DOCID = "jobsCount"
PROJECT_DOCID = "projectInfo"


class StorageException(Exception): pass



class Storage(object):
    "Facade for MongoDB that is specific for this aplication."
    
    
    def __init__(self, host='localhost', port=27017):
        self.log = logging.getLogger('kts46.storage.mongodb')
        self.log.debug("Creating connection to Mongodb server: %s:%i.", host, port)
        self.server = pymongo.Connection(host, port)
        self.log.info("Connection created: %s:%i.", host, port)
        
        
    def createProject(self, projectName):
        """Creates project with specified name.

        A StorageException will be raised if project already exists.
        Arguments:
          projectName [string] - name of project to create.
          
        Returns SimulationProject instance."""

        self.log.info("Creating project: %s.", projectName)
        if projectName in self:
            msg = "Couldn't create project because it already exists."
            msg += " Project name: {0}.".format(projectName)
            raise StorageException(msg)

        db = self.server[projectName]
        p = SimulationProject(self.server, projectName, self.log)
        #p.initialize()
        return p


    def __getitem__(self, key):
        if key not in self:
            msg = "Couldn't get project '{0}' because it doesn't exists.".format(key)
            self.log.warning(msg)
            raise KeyError(msg)
        return SimulationProject(self.server, key, self.log)


    def __contains__(self, item):
        "Checks whether project with specified name already exists. Returns bool."
        # local and admin are utility databases.
        if item not in ['local', 'admin'] and item in self.server.database_names():
            if self.server[item].info.find_one('project') is not None:
                return True
        return False


    def __delitem__(self, key):
        """Deletes project with specified name.

        Raises KeyError if project doesn't exist."""
        
        if key in self:
            self.log.debug("Deleting project '{0}'.".format(key))
            self.server.drop_database(key)
            self.log.info("Project '{0}' deleted.".format(key))
        else:
            msg = "Couldn't delete project '{0}' because it doesn't exists.".format(key)
            self.log.warning(msg)
            raise KeyError(msg)

    def getProjectNames(self):
        """Returns list of projects in storage.

        Returns list of strings."""
        # 'in self' returns true only for projects, not any databases.
        return filter(lambda x: x in self, [p for p in self.server.database_names()])



class SimulationProject(object):
    "Represents a simulation project stored in database."

    def __init__(self, dbserver, name, log):
        self.server = dbserver
        self.name = name
        self.db = self.server[name]
        self.log = log
        
        # ensure that database exists
        if self.db.info.find_one('project') is None:
            self.db.info.insert({'_id':'project', 'name': name})
        

    #def initialize(self):
    #    "Initializes project infrastructure in database by creating required documents."
    #    self.db.project.insert({"jobs": {}, '_id':PROJECT_DOCID})

    def addJob(self, jobName, definition):
        """Adds job with specified YAML definition to project.

        StorageException will be raised if job with specified name already exists.
        Arguments:
            jobName -- job name.
            definition -- definition of job written in YAML.
        """

        # Check for job duplication.
        if jobName in self:
            msg = "Couldn't add job '{0}' to project '{1}' because it already exists."
            raise CouchDBServerException(msg.format(jobName, self.name))

        job = SimulationJob(self, jobName, definition)
    
        return job
    

    def __getitem__(self, key):
        if key not in self:
            msg = "Couldn't get job '{0}' from project '{1}' because it doesn't exists."
            msg = msg.format(key, self.name)
            self.log.warning(msg)
            raise KeyError(msg)
        return SimulationJob(self, key)


    def __contains__(self, item):
        "Checks whether job with provided name exists in project."
        return self.db.jobs.find_one(item) is not None


    def __delitem__(self, key):
        """Deletes job with specified name if it exists.
        Otherwise throws KeyError."""
        if key not in self:
            msg = "Couldn't delete job '{0}' in project '{1}' because it doesn't exist." 
            raise KeyError(msg.format(key, self.name))

        self.db.progresses.remove(key)
        self.db.statistics.remove(key)
        self.db.jobs.remove(key)
        self.db.states.remove({'job': key})
        
        
    #def getDocument(self, docid):
    #    "Gets document from database with specified id."
    #    return self.db[docid]


    #def containsDocument(self, docid):
    #    "Checks whether document with specified id exists in database."
    #    return docid in self.db


    def getJobsList(self):
        "Gets list of project jobs names."
        return map(lambda x: x['_id'], self.db.jobs.find(fields=['_id']))
    
    def getJobs(self):
        "Gets project jobs."
        jobs = [ ]
        for jobName in self.getJobsList():
            jobs.append(self[jobName])
        return jobs



class SimulationJob(object):

    def __init__(self, project, name, definition=None):
        self.project = project
        self.db = project.db
        self.name = name
        self.progress = None
        self.statistics = None
        self.definition = definition
        if definition is None:
            self._load()
        else:
            self._create()

    def _create(self):
        # Store simulation parameters.
        objData = yaml.safe_load(self.definition)
        simParams = objData['simulationParameters']
        simulationTime = simParams['duration']
        simulationStep = simParams['stepDuration']
        simulationBatchLength = simParams['batchLength']
        self.simulationParameters = simParams

        self.db.jobs.insert({'name': self.name, 'yaml': self.definition,
                             'type': 'job', 'simulationParameters': simParams,
                             '_id': self.name})
        self.db.progresses.insert({'_id': self.name,
            #'job': self.docid,
            'totalSteps': math.floor(simulationTime / simulationStep),
            'batches': math.floor(simulationTime / simulationStep / simulationBatchLength),
            'done': 0,
            'currentFullState': ''})

        self.statistics = {'_id': self.name,
            'average': 1.1, 'stdeviation': 1.1,
            'averageSpeed': 1.1,
            'stallTimes': {},
            'finished': False }
        self.db.statistics.insert(self.statistics)


    def _load(self):
        doc = self.db.jobs.find_one(self.name)

        self.definition = doc['yaml']
        self.simulationParameters = doc['simulationParameters']

        self.progress = self.db.progresses.find_one(self.name)
        self.statistics = self.db.statistics.find_one(self.name)


    def getStateDocumentId(self, time):
        "Returns document id of state for specified time."
        return "".join((self.name, ',', time))


    def __contains__(self, key):
        "Checks whether state with specified id exists."
        id = self.getStateDocumentId(key)
        return self.db.states.find_one(id, fields={})


    def __getitem__(self, key):
        "Gets state with specified id."
        id = self.getStateDocumentId(key)
        s = self.db.states.find_one(id)
        if s is None:
            raise KeyError("There is no state with specified time: {0}.".format(key))
        return s


    def save(self):
        if self.progress is not None:
             self.db.progresses.save(self.progress)
        if self.statistics is not None:
             self.db.statistics.save(self.statistics)


class StateStorage(object):
    
    def __init__(self, job, fullStateGeneratorCallback=None, batchLength=None):
        self.db = job.db
        self.job = job
        self.buffer = []
        if batchLength is None:
            self.bufferSize = job.simulationParameters['batchLength']
        else:
            self.bufferSize = batchLength
        self.fullStateGeneratorCallback = fullStateGeneratorCallback

        
    def add(self, time, data):
        d = dict(data)
        d['time'] = time
        d['job'] = self.job.name
        d['_id'] = self.job.getStateDocumentId(str(time))
        
        self.buffer.append(d)
        if len(self.buffer) >= self.bufferSize:
            self.dump()


    def dump(self):
        if len(self.buffer) > 0:
            self.job.progress['done'] += len(self.buffer)
            #self.job.progress['currentStateId'] = str(self.bulk_queue[-1]['time'])

            if self.fullStateGeneratorCallback is not None:
                self.job.progress['currentFullState'] = self.fullStateGeneratorCallback()
            else:
                self.job.progress['currentFullState'] = ''

            cars = [ ]
            for state in self.buffer:
                for carId, car in state['cars'].items():
                    #car['stateid'] = state['_id']
                    car['job'] = state['job']
                    car['time'] = state['time']
                    car['carid'] = carId
                    cars.append(car)
                del state['cars']

            # self.buffer.append(self.job.progress)
            self.db.progresses.save(self.job.progress)
            self.db.states.insert(self.buffer)
            self.db.cars.insert(cars)
            self.buffer = []

    def close(self): self.dump()
