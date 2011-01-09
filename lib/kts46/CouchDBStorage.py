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

import couchdb, couchdb.design, json, logging, yaml, math
import CouchDBViewDefinitions


class CouchDBStorageException(Exception): pass


class CouchDBStorage:
    "Wraps functionality of CouchDB for specific purposes of this application."

    def __init__(self, serverPath):
        """Initializes storage instance.

        Arguments:
          serverPath [string] - network path to CouchDB server, e.g. http://192.168.1.2:5984.
        """

        self.logger = logging.getLogger('kts46.CouchDBStorage')
        self.logger.debug('Creating server...')
        self.server = couchdb.Server(serverPath)
        self.logger.info('Server created.')

    def createProject(self, projectName):
        """Creates database project with specified name.

        A CouchDBStorageException will be raised if project already exists.
        Arguments:
          projectName [string] - name of project to create."""

        if projectName in self.server:
            msg = "Couldn't create project because it already exists."
            msg += ' Project name: %s.' % projectName
            raise CouchDBStorageException(msg)

        project = self.server.create(projectName)
        # Create special document to store amount of jobs created.
        #project[SimulationProject.jobsCountDocId] = {'lastId' : 0}
        #self._createViews(projectName)
        p = SimulationProject(self.server, projectName, self.logger)
        p.initialize()
        return p

    def __getitem__(self, key):
        if key not in self:
            msg = "Couldn't get project '%s' because it doesn't exists." % key
            self.logger.warning(msg)
            raise KeyError(msg)
        return SimulationProject(self.server, key, self.logger)

    def __contains__(self, item):
        # Explicitly skip internal databases, because they are recognised as
        # databases, but throws an error while creation of db.
        if item[0] == '_':
            return False
        if item in self.server:
            db = self.server[item]
            if SimulationProject.jobsCountDocId in db:
                return True
        return False

    def __delitem__(self, key):
        """Deletes project with specified name if it exists. Otherwise raises
        RPCServerException."""
        if key in self:
            self.logger.debug("Deleting project '%s'." % key)
            del self.server[key]
            self.logger.info("Project '%s' deleted." % key)
        else:
            msg = "Couldn't delete project '%s' because it doesn't exists." % key
            self.logger.warning(msg)
            raise KeyError(msg)


    def getProjects(self):
        "Returns list of projects in storage."
        # 'in self' returns true only for projects, not any databases.
        return filter(lambda x: x in self, [p for p in self.server])


class SimulationProject:
    "Represents a simulation project stored in database."

    jobsCountDocId = 'jobsCount'
    lastId = 'lastId'
    jobsListView = 'manage/jobs'
    statesView = 'manage/states'
    jobProgressDocId = '%sProgress'
    stateDocIdFormat = 's{job}_{state}'
    statisticsDocIdFormat = '{job}Statistics'

    def __init__(self, couchServer, name, logger):
        self.server = couchServer
        self.name = name
        self.db = self.server[name]
        self.logger = logger


    def initialize(self):
        "Initializes project infrastructure in database by creating required documents."
        self.db[SimulationProject.jobsCountDocId] = {'lastId' : 0}
        self._createViews()

    def _createViews(self):
        "Creates all requires views in the database."

        defsStr = CouchDBViewDefinitions.definitions
        defs = [ ]
        for defStr in defsStr:
            defs.append(couchdb.design.ViewDefinition(defStr['doc'], defStr['view'], defStr['map']))
        couchdb.design.ViewDefinition.sync_many(self.db, defs)

        # To speed things upon first request here I will try to call each view
        # manually, so while inserting values indexes will be updated and first
        # query to views will be fast.
        len(self.db.view("basicStats/addCar"))
        len(self.db.view("basicStats/deleteCar"))
        len(self.db.view("manage/jobs"))
        len(self.db.view("manage/states"))


    def getNewJobId(self):
        """Creates new job id.

        It is guaranteed that there will be no dublicates, because after
        generation new id is written to database and CouchDB will not allow two
        same job ids because of revision number conflicts. However an exception
        will be thrown by underlying couchdb bindings and this function currently
        doesn't do anything about that."""

        countDoc = self.db[SimulationProject.jobsCountDocId]
        countDoc[SimulationProject.lastId] += 1
        self.db[SimulationProject.jobsCountDocId] = countDoc
        return countDoc[SimulationProject.lastId]

    def addJob(self, jobName, definition):
        """Adds job with sepcified YAML definition to project.

        CouchDBStorageException will be raised if job with specified name already exists.
        Arguments:
            jobName -- job name.
            definition -- definition of job written in YAML.
        """

        # Check for job dublication.
        if jobName in self:
            msg = "Couldn't add job '%s' to project '%s' because it already exists."
            raise CouchDBServerException(msg % (jobName, self.name))

        job = SimulationJob(self, jobName)
        job.initialize(definition)

        return job

    def __getitem__(self, key):
        filteredJobs = self.db.view(SimulationProject.jobsListView)[key]
        if len(filteredJobs) == 0:
            msg = "Couldn't get job '%s' from project '%s' because it doesn't exists."
            msg %= (key, self.name)
            self.logger.warning(msg)
            raise KeyError(msg)
        row = list(filteredJobs)[0]
        return SimulationJob(self, key, row['value'])

    def __contains__(self, item):
        "Checks whether job with provided name exists in project."
        return len(self.db.view(SimulationProject.jobsListView)[item]) > 0

    def __delitem__(self, key):
        """Deletes job with specified name if it exists.
        Otherwise throws CouchDBStorageException."""
        # proj = self.server[projectName]
        jobRows = self.db.view(SimulationProject.jobsListView)[key]
        if len(jobRows) == 0:
            raise CouchDBStorageException(
                "Couldn't delete job '%s' in project '%s' because it doesn't exist." %
                (key, self.name))
        for jobRow in jobRows:
            jobId = int(jobRow['value'][1:]) # Skip first 'j' letter.
            jobIdStr = jobRow['value']
            # Delete job progress.
            del self.db[SimulationProject.jobProgressDocId % jobIdStr]
            # Delete job statistics.
            del self.db[SimulationProject.statisticsDocIdFormat.format(job=jobIdStr)]
            # Delete job itself.
            del self.db[jobIdStr]
            # Delete simulated states.
            states = self.db.view(SimulationProject.statesView)[jobId]
            for s in states:
                del self.db[s['value']]


    def getDocument(self, docid):
        "Gets document from database with specified id."
        return self.db[docid]


    def containsDocument(self, docid):
        "Checks whether document with specified id exists in database."
        return docid in self.db


    def getJobsList(self):
        "Gets list of project jobs names."
        names = [ ]
        jobs = self.db.view(SimulationProject.jobsListView)
        for job in jobs:
            names.append(job['key'])
        return names

    def getJobs(self):
        "Gets project jobs."
        jobs = [ ]
        for jobName in self.getJobsList():
            jobs.append(self[jobName])
        return jobs


class SimulationJob:

    def __init__(self, project, name, id=None):
        self.project = project
        self.name = name
        self.id = None
        self.docid = None
        self.progress = None
        self.statistics = None
        self.progressId = None
        self.statisticsId = None
        if id is not None:
            self._initializeFromDb(id)

    def initialize(self, definition):
        self.definition = definition

        # Store simulation parameters.
        objData = yaml.safe_load(self.definition)
        simParams = objData['simulationParameters']
        simulationTime = simParams['duration']
        simulationStep = simParams['stepDuration']
        simulationBatchLength = simParams['batchLength']
        self.simulationParameters = simParams

        self._setId()
        self.project.db[self.docid] = {'name': self.name, 'yaml': self.definition,
                                'type': 'job', 'simulationParameters': simParams}
        self.progress = {'job': self.docid,
            'totalSteps': math.floor(simulationTime / simulationStep),
            'batches': math.floor(simulationTime / simulationStep / simulationBatchLength),
            'done': 0,
            'currentFullState': ''}
        self.project.db[self.progressId] = self.progress

        self.statistics = {'average': None, 'stdeviation': None, 'finished': False}
        self.project.db[self.statisticsId] = self.statistics

    def _initializeFromDb(self, id):
        self._setId(None, id)
        db = self.project.db
        doc = db[id]

        self.definition = doc['yaml']
        self.simulationParameters = doc['simulationParameters']

        self.progress = db[self.progressId]
        self.statistics = db[self.statisticsId]


    def getStateDocumentId(self, stateId):
        "Returns document id of specified state."
        return SimulationProject.stateDocIdFormat.format(job=self.id, state=stateId)


    def __contains__(self, key):
        "Checks whether state with specified id exists."
        return self.project.containsDocument(self.getStateDocumentId(key))


    def __getitem__(self, key):
        "Gets state with specified id."
        return self.project.getDocument(self.getStateDocumentId(key))


    def _setId(self, id=None, docid=None):
        if id is None and docid is not None:
            self.docid = docid
            self.id = int(docid[1:])
        elif id is not None and docid is None:
            self.id = id
            self.docid = 'j' + str(self.id)
        elif id is None and docid is None:
            self.id = self.project.getNewJobId()
            self.docid = 'j' + str(self.id)

        # Set child docs ids.
        self.progressId = SimulationProject.jobProgressDocId % self.docid
        self.statisticsId = SimulationProject.statisticsDocIdFormat.format(job=self.docid)

    def save(self):
        if self.progress is not None:
             self.project.db[self.progressId] = self.progress
        if self.statistics is not None:
             self.project.db[self.statisticsId] = self.statistics
