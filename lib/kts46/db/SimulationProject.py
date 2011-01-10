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

import couchdb.design
import CouchDBViewDefinitions
from . import *
from SimulationJob import SimulationJob

class SimulationProject:
    "Represents a simulation project stored in database."

    def __init__(self, couchServer, name, logger):
        self.server = couchServer
        self.name = name
        self.db = self.server[name]
        self.logger = logger


    def initialize(self):
        "Initializes project infrastructure in database by creating required documents."
        self.db[JOBS_COUNT_DOCID] = {'lastId' : 0}
        self.db[PROJECT_DOCID] = {"jobs": {}}
        self._createViews()

    def _createViews(self):
        "Creates all requires views in the database."

        defsStr = CouchDBViewDefinitions.definitions
        defs = [ ]
        for defStr in defsStr:
            defs.append(couchdb.design.ViewDefinition(defStr['doc'], defStr['view'], defStr['map']))
        couchdb.design.ViewDefinition.sync_many(self.db, defs)


    def getNewJobId(self):
        """Creates new job id.

        It is guaranteed that there will be no dublicates, because after
        generation new id is written to database and CouchDB will not allow two
        same job ids because of revision number conflicts. However an exception
        will be thrown by underlying couchdb bindings and this function currently
        doesn't do anything about that."""

        countDoc = self.db[JOBS_COUNT_DOCID]
        countDoc[LAST_ID] += 1
        self.db[JOBS_COUNT_DOCID] = countDoc
        return countDoc[LAST_ID]

    def addJob(self, jobName, definition):
        """Adds job with specified YAML definition to project.

        CouchDBStorageException will be raised if job with specified name already exists.
        Arguments:
            jobName -- job name.
            definition -- definition of job written in YAML.
        """

        # Check for job duplication.
        if jobName in self:
            msg = "Couldn't add job '%s' to project '%s' because it already exists."
            raise CouchDBServerException(msg % (jobName, self.name))

        job = SimulationJob(self, jobName)
        job.initialize(definition)
        
        p = self.db[PROJECT_DOCID]
        p['jobs'][jobName] = job.docid
        self.db.update([p])

        return job

    def __getitem__(self, key):
        p = self.db[PROJECT_DOCID]
        if key not in p['jobs']:
            msg = "Couldn't get job '%s' from project '%s' because it doesn't exists."
            msg %= (key, self.name)
            self.logger.warning(msg)
            raise KeyError(msg)
        jobid = p['jobs'][key]
        return SimulationJob(self, key, jobid)

    def __contains__(self, item):
        "Checks whether job with provided name exists in project."
        return item in self.db[PROJECT_DOCID]['jobs']

    def __delitem__(self, key):
        """Deletes job with specified name if it exists.
        Otherwise throws CouchDBStorageException."""
        p = self.db[PROJECT_DOCID]
        if key not in p['jobs']:
            raise CouchDBStorageException(
                "Couldn't delete job '%s' in project '%s' because it doesn't exist." %
                (key, self.name))

        # Remove record from project description.            
        del p['jobs'][key]
        self.db.update([p])

        jobIdStr = p['jobs'][key]
        jobId = jobIdStr[1:] # Skip first 'j' letter.
        # Delete job progress.
        del self.db[JOB_PROGRESS_DOCID_FORMAT.format(job=jobIdStr)]
        # Delete job statistics.
        del self.db[STATISTICS_DOCID_FORMAT.format(job=jobIdStr)]
        # Delete job itself.
        del self.db[jobIdStr]
        # Delete simulated states.
        states = self.db.view(STATES_VIEW)[jobId]
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
        return self.db[PROJECT_DOCID]['jobs'].keys()
    
    def getJobs(self):
        "Gets project jobs."
        jobs = [ ]
        for jobName in self.getJobsList():
            jobs.append(self[jobName])
        return jobs

