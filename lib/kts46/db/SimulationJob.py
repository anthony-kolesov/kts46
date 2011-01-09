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
from . import *
#import kts46.CouchDBStorage

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
        return STATE_DOCID_FORMAT.format(job=self.id, state=stateId)


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
        self.progressId = JOB_PROGRESS_DOCID_FORMAT % self.docid
        self.statisticsId = STATISTICS_DOCID_FORMAT.format(job=self.docid)

    def save(self):
        if self.progress is not None:
             self.project.db[self.progressId] = self.progress
        if self.statistics is not None:
             self.project.db[self.statisticsId] = self.statistics
