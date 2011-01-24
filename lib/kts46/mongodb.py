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

"""Wraps functionality of MongoDB to provide storage facility specific to
application requirements.

:class:`Storage` represents MongoDB instance. It acts like a type specific
dictionary for `SimulationProject` s which represent databases on server.
On their hand projects act like type specific dictionaries for
`SimulationJob` s. And jobs act like dictionaries for their
`SimulationState` s.

"""

import logging
import math # Math.floor
import pymongo # connect with db
import yaml # parse model definition


class StorageException(Exception):
    """Exception for error that happen in operations with storage. For example
    if there is an attempt to create project with name that already exists."""
    pass


class Storage(object):
    """Facade for MongoDB that is specific for this application.
    Acts like a dictionary for projects.
    """

    def __init__(self, host='localhost', port=27017):
        """Initializes storage and connects to the server.

        :param host: network address of database. Can be a name or IP address.
        :type host: str
        :param port: port of database on a host.
        :type port: int
        """
        self.log = logging.getLogger('kts46.storage.mongodb')
        self.log.debug("Creating connection to Mongodb server: %s:%i.", host, port)
        self.server = pymongo.Connection(host, port)
        self.log.info("Connection created: %s:%i.", host, port)


    def createProject(self, projectName):
        """Creates project with specified name.

        :param projectName: name of project to create.
        :type projectName: str
        :returns: newly created project.
        :rtype: kts46.mongodb.SimulationProject
        :raises StorageException: If project already exists.
        """

        self.log.info("Creating project: %s.", projectName)
        if projectName in self:
            msg = "Couldn't create project because it already exists."
            msg += " Project name: {0}.".format(projectName)
            raise StorageException(msg)

        db = self.server[projectName]
        p = SimulationProject(self.server, projectName, self.log)
        return p


    def __getitem__(self, key):
        """Gets SimulationProject with specified name.

        :param key: project name.
        :type key: str
        :returns: Project with specified name.
        :rtype: kts46.mongodb.SimulationProject
        :raises KeyError: if project with specified name doesn't exists.
        """

        if key not in self:
            msg = "Couldn't get project '{0}' because it doesn't exists.".format(key)
            self.log.warning(msg)
            raise KeyError(msg)
        return SimulationProject(self.server, key, self.log)


    def __contains__(self, item):
        """Checks whether project with specified name already exists.

        :param item: project name to check for existence.
        :type item: str
        :rtype: bool
        """

        # local and admin are utility databases.
        if item not in ['local', 'admin'] and item in self.server.database_names():
            if self.server[item].info.find_one('project') is not None:
                return True
        return False


    def __delitem__(self, key):
        """Deletes project with specified name.

        :param key: name of project to delete.
        :type key: str
        :raises KeyError: if project doesn't exist
        """

        if key in self:
            self.log.debug("Deleting project '{0}'.".format(key))
            self.server.drop_database(key)
            self.log.info("Project '{0}' deleted.".format(key))
        else:
            msg = "Couldn't delete project '{0}' because it doesn't exists.".format(key)
            self.log.warning(msg)
            raise KeyError(msg)


    def getProjectNames(self):
        """Returns list of names of projects in storage.

        :rtype: list of strings."""
        # '__contains__' returns true only for projects, not any databases.
        return filter(self.__contains__, [p for p in self.server.database_names()])
        #return filter(self.__contains__ lambda x: x in self, [p for p in self.server.database_names()])



class SimulationProject(object):
    "Represents a simulation project stored in database."

    def __init__(self, dbserver, name, log):
        """Creates new instance of :class:`SimulationProject` class. If project
        doesn't exists on the server it will be created.

        :param dbserver: mongodb connection.
        :param name: project name.
        :param log: logger.
        """
        self.server = dbserver
        self.name = name
        self.db = self.server[name]
        self.log = log

        # ensure that database exists
        if self.db.info.find_one('project') is None:
            self.db.info.insert({'_id':'project', 'name': name})
            self.db.cars.create_index([('job',pymongo.ASCENDING),('state',pymongo.ASCENDING)])
            self.db.cars.create_index([('job',pymongo.ASCENDING),('carid',pymongo.ASCENDING)])


    def addJob(self, jobName, definition):
        """Adds job with specified YAML definition to project.

        :param jobName: job name
        :type jobName: str
        :param definition: definition of job written in YAML.
        :type definition: str
        :returns: created job.
        :rtype: SimulationJob
        :raises StorageException: if job with specified name already exists.
        """

        # Check for job duplication.
        if jobName in self:
            msg = "Couldn't add job '{0}' to project '{1}' because it already exists."
            raise StorageException(msg.format(jobName, self.name))
        job = SimulationJob(self, jobName, definition)
        return job


    def __getitem__(self, key):
        """Gets job with specified name.

        :param key: name of job to get.
        :type key: str
        :returns: job with specified name
        :rtype: SimulationJob
        :raises KeyError: if job with specified name doesn't exists.
        """
        if key not in self:
            msg = "Couldn't get job '{0}' from project '{1}' because it doesn't exists."
            msg = msg.format(key, self.name)
            self.log.warning(msg)
            raise KeyError(msg)
        return SimulationJob(self, key)


    def __contains__(self, item):
        """Checks whether job with provided name exists in project.

        :param item: Name of job to check for.
        :type item: str
        :rtype: bool
        """
        return self.db.jobs.find_one(item) is not None


    def __delitem__(self, key):
        """Deletes job with specified name.

        :param key: name of job to delete.
        :type key: str
        :raises KeyError: if job with specified name doesn't exists.
        """
        if key not in self:
            msg = "Couldn't delete job '{0}' in project '{1}' because it doesn't exist."
            raise KeyError(msg.format(key, self.name))

        self.db.progresses.remove(key)
        self.db.statistics.remove(key)
        self.db.jobs.remove(key)
        self.db.states.remove({'job': key})


    def getJobsNames(self):
        """Gets list of project jobs names.

        :returns: names of jobs of this project.
        :rtype: list of strings
        """
        return map(lambda x: x['_id'], self.db.jobs.find(fields=['_id']))


    def getJobs(self):
        """Gets project jobs.

        :returns: list of project jobs.
        :rtype: list of :class:`SimulationJob`
        """
        jobs = [ ]
        for jobName in self.getJobsNames():
            jobs.append(self[jobName])
        return jobs



class SimulationJob(object):
    "Job to simulate."

    def __init__(self, project, name, definition=None):
        """Create new :class:`SimulationJob` instance .

        :param project: project to which job belongs.
        :type project: SimulationProject
        :param name: name of this job.
        :type name: str
        :param definition: YAML definition of job. If it is omitted than job
         will be loaded from database.
        :type definition: str
        """
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
        "Creats new job on the server from definition."
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
            'currentFullState': '',
            'basicStatistics': False, 'idleTimes': False, 'throughput': False,
            'fullStatistics': False,
            'jobname': self.name
        })

        self.statistics = {'_id': self.name,
            'average': None, 'stdeviation': None,
            'averageSpeed': None,
            'idleTimes': {},
            'thoughput': [ ],
            'finished': False }
        self.db.statistics.insert(self.statistics)


    def _load(self):
        "Loads existing job from the server."
        doc = self.db.jobs.find_one(self.name)

        self.definition = doc['yaml']
        self.simulationParameters = doc['simulationParameters']

        p = self.db.progresses.find_one(self.name)
        self.progress = p
        self.statistics = self.db.statistics.find_one(self.name)

        # Update old documents
        updated = False
        if 'throughput' not in self.statistics:
            self.statistics['throughput'] = []
            updated = True

        if 'basicStatistics' not in p:
            if 'finished' in self.statistics:
                p['basicStatistics'] = self.statistics['finished']
            else:
                p['basicStatistics'] = False
            updated = True
        if 'idleTiems' not in p:
            p['idleTimes'] = len(self.statistics['idleTimes']) > 0
            updated = True
        if 'throughput' not in p:
            if 'throughput' in self.statistics:
                p['throughput'] = len(self.statistics['throughput']) > 0
            else:
                p['throughput'] = False
            updated = True
        if 'fullStatistics' not in p:
            p['fullStatistics'] = (p['basicStatistics'] and
                                   p['idleTimes'] and
                                   p['throughput'])
            updated = True
        if 'jobname' not in p:
            p['jobname'] = self.name
            updated = True

        if updated: self.save()


    def getStateDocumentId(self, time):
        """Returns document id of state for specified time.

        :param time: time for which to get state.
        :type time: str or float
        :returns: document id of state for specified time.
        :rtype: str
        """
        return ",".join((self.name, time))


    def __contains__(self, key):
        """Checks whether state with specified id exists.

        :param key: time of state to check.
        :type key: str or float
        :rtype: bool
        """
        id = self.getStateDocumentId(key)
        return self.db.states.find_one(id, fields={})


    def __getitem__(self, key):
        """Gets state with specified id.

        :param key: time of state to get.
        :type key: str or float
        :rtype: dict
        :returns: state of model at specified time.
        :raises KeyError: there is no state saved for specified time.
        """
        id = self.getStateDocumentId(key)
        s = self.db.states.find_one(id)
        if s is None:
            raise KeyError("There is no state with specified time: {0}.".format(key))
        return s


    def save(self):
        "Saves progress and statistics to server."
        if self.progress is not None:
             self.db.progresses.save(self.progress)
        if self.statistics is not None:
             self.db.statistics.save(self.statistics)

    def round(self, value):
        """Provides centralised way to round values for required precision.

        :param value: value to round.
        :type value: float
        :returns: value rounded with required precision.
        :rtype: float
        """
        return round(value, 6)


class StateStorage(object):
    "Represents storage for simulation states."

    def __init__(self, job, fullStateGeneratorCallback=None, batchLength=None):
        """Creates new instance of :class:`StateStorage` class.

        :param job: job for which this storage belongs.
        :type job: SimulationJob
        :param fullStateGeneratorCallback: function that returns current full
         state of the model.
        :type fullStateGeneratorCallback: callable
        :param batchLength: length of batches that to send to the server.
         If None then length from job parameters will be used.
        :type batchLength: int
        """
        self.db = job.db
        self.job = job
        self.buffer = []
        if batchLength is None:
            self.bufferSize = job.simulationParameters['batchLength']
        else:
            self.bufferSize = batchLength
        self.fullStateGeneratorCallback = fullStateGeneratorCallback


    def add(self, time, data):
        """Adds state to the storage.

        :param time: time for which to save state.
        :type time: float
        :param data: model state that will be saved.
        :type data: dic
        """
        d = dict(data)
        d['time'] = time
        d['job'] = self.job.name
        d['_id'] = self.job.getStateDocumentId(str(time))

        self.buffer.append(d)
        if len(self.buffer) >= self.bufferSize:
            self.dump()


    def dump(self):
        """Dump states saved in a buffers to server. This method is called by
        ``add`` when length of buffer is more than batchLength and by
        ``close`` method."""
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

    def close(self):
        "Save all unsaved data to server."
        self.dump()
