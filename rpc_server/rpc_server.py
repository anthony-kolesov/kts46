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

import logging, logging.handlers, couchdb, couchdb.client, sys, yaml, math
from SimpleXMLRPCServer import SimpleXMLRPCServer
from ConfigParser import SafeConfigParser

sys.path.append('../lib/')
from kts46 import Car, Road, SimpleSemaphore, Model, CouchDBStorage,\
    CouchDBViewDefinitions
from kts46.serverApi import RPCServerException


def init():
    """Initializes server infrastructure. Returns (SafeConfigParser, logger)."""

    configFiles = ('../config/common.ini', '../config/rpc_server.ini')
    # Create configuration.
    logging.debug('Reading configuration.')
    cfg = SafeConfigParser()
    cfg.read(configFiles)

    # Configure logging.
    logging.getLogger('').setLevel(logging.INFO)
    logging.basicConfig(format=cfg.get('log', 'format'),
                    datefmt=cfg.get('log', 'dateFormat'),
                    filename=cfg.get('log', 'filename'),
                    filemode=cfg.get('log', 'filemode'))

    # Define a log handler for rotating files.
    rfhandler = logging.handlers.RotatingFileHandler(cfg.get('log', 'filename'),
        maxBytes=cfg.get('log', 'maxBytesInFile'),
        backupCount=cfg.get('log', 'backupCountOfFile'))
    rfhandler.setLevel(logging.INFO)
    rfhandler.setFormatter(logging.Formatter(cfg.get('log', 'format')))
    logging.getLogger('').addHandler(rfhandler)

    logger = logging.getLogger(cfg.get('log', 'loggerName'))

    return (cfg, logger)


def hello(msg):
    "Test method to check that server is working fine."
    return '''Hello you too! This is simple XML-RPC server for kts46.
            You\'ve said: [''' + msg + ']'

def shutdown():
    logging.getLogger('').info('Shutdown server.')
    # sys.exit(1)
    server.shutdown()
    logging.getLogger('').info('Shutdowned server.')


class ModelParams:

    def __init__(self):
        self.carGenerationInterval = 3.0
        self.safeDistance = 5.0
        self.maxSpeed = 20.0
        self.minSpeed = 10.0


#class RPCServerException(Exception):
#    pass


class CouchDBProxy:

    jobsCountDocId = 'jobsCount'
    lastId = 'lastId'
    jobProgressDocId = '%sProgress'
    jobsListView = 'manage/jobs'
    statesView = 'manage/states'

    def __init__(self, cfg):
        self.cfg = cfg
        self.logger = logging.getLogger('kts46.rpc_server.couchdb')
        self.server = couchdb.Server(cfg.get('couchdb', 'dbaddress'))

    def _createViews(self, projectName):
        "Creates all requires views for the database."

        defsStr = CouchDBViewDefinitions.definitions
        defs = [ ]
        for defStr in defsStr:
            defs.append(couchdb.design.ViewDefinition(defStr['doc'],
                defStr['view'], defStr['map']))
        couchdb.design.ViewDefinition.sync_many(self.server[projectName], defs )


    def getNewJobId(self, projectName):
        """Creates new job id.

        It is guaranteed that there will be no dublicates, because after
        generation new id is written to database and CouchDB will not allow two
        same job ids because of revision number conflicts.
        RPCServerException is thrown if project doesn't exist."""

        if projectName not in self.server:
            raise RPCServerException("Couldn't get new job id because project doesn't exist.")
        project = self.server[projectName]
        countDoc = project[CouchDBProxy.jobsCountDocId]
        countDoc[CouchDBProxy.lastId] = countDoc[CouchDBProxy.lastId] + 1
        project[CouchDBProxy.jobsCountDocId] = countDoc
        return countDoc[CouchDBProxy.lastId]


    def createProject(self, projectName):
        """Create in database project with specified name.

        An exception will be raised it project already exists.
        Arguments:
            projectName -- name of peoject to create."""
        if projectName not in self.server:
            project = self.server.create(projectName)
            # Create special document to store amount of jobs created.
            project[CouchDBProxy.jobsCountDocId] = {'lastId' : 0}
            self._createViews(projectName)
        else:
            msg = "Couldn't create project because it already exists."
            msg += ' Project name: %s.' % projectName
            raise RPCServerException(msg)


    def projectExists(self, projectName):
        "Checks whether project with specified name already exists."
        return projectName in self.server


    def deleteProject(self, projectName):
        """Deletes project with specified name if it exists. Otherwise raises
        RPCServerException."""
        if projectName in self.server:
            self.logger.debug("Deleting project '%s'." % projectName)
            del self.server[projectName]
            self.logger.info("Project '%s' deleted." % projectName)
        else:
            msg = "Couldn't delete project '%s' because it doesn't exists." % projectName
            self.logger.warning(msg)
            raise RPCServerException(msg)


    def addJob(self, projectName, jobName, definition):
        """Adds specified job to project.

        RPCServerException will be raised if project doesn't exist or job with
        specified name already exists.
        Arguments:
            projectName -- name of model project.
            jobName -- job name.
            definition -- definition of job written in YAML.
        """
        if projectName not in self.server:
            raise RPCServerException("""Couldn't add job '%s', because project
'%s' doesn't exist.""" % (jobName, projectName))

        # Check for job dublication.
        if self.jobExists(projectName, jobName):
            raise RPCServerException("""Couldn't add job '%s' to project '%s'
because it already exists.""" % (jobName, projectName) )

        db = self.server[projectName]

        # Store simulation parameters.
        objData = yaml.safe_load(definition)
        simulationTime = objData['simulationTime']
        simulationStep = objData['simulationStep']

        jobId = 'j' + str(self.getNewJobId(projectName))
        db[jobId] = {'name': jobName, 'yaml': definition, 'type': 'job',
            'simulationTime': simulationTime, 'simulationStep': simulationStep}
        db[CouchDBProxy.jobProgressDocId % jobId] = {'job': jobId,
            'totalSteps': math.floor(simulationTime/simulationStep),
            'done': 0 }


    def jobExists(self, projectName, jobName):
        """Checks whether job with provided name exists in project.

        RPCServerExceptpion is thrown if project doesn't exist."""
        if projectName not in self.server:
            raise RPCServerException("Project '%s' doesn't exist." % projName)
        db = self.server[projectName]
        return len(db.view(CouchDBProxy.jobsListView)[jobName]) > 0


    def deleteJob(self, projectName, jobName):
        "Deletes job with specified name if it exists. Otherwise throws RPCServerException."
        if projectName not in self.server:
            raise RPCServerException("Project '%s' doesn't exist." % projectName)
        proj = self.server[projectName]
        jobRows = proj.view(CouchDBProxy.jobsListView)[jobName]
        if len(jobRows) == 0:
            raise RPCServerException(
                "Couldn't delete job '%s' in project '%s' because it doesn't exist." %
                (jobName, projectName) )
        for jobRow in jobRows:
            jobId = int(jobRow['value'][1:]) # Skip first 'j' letter.
            del proj[CouchDBProxy.jobProgressDocId % ( 'j'+str(jobId) )]
            del proj['j'+str(jobId)]
            states = proj.view(CouchDBProxy.statesView)[jobId]
            for s in states:
                del proj[s['value']]


    def runJob(self, projectName, jobName):
        """Simulates model for the specified time duration."""

        if projectName not in self.server:
            raise RPCServerException("Project '%s' doesn't exist." % projectName)
        db = self.server[projectName]

        # Use only first job. There acually can be only one.
        jobsViewResult = db.view(CouchDBProxy.jobsListView)[jobName]
        jobIdStr = list(jobsViewResult)[0]['value'][1:]
        jobId = int(jobIdStr)

        # Prepare infrastructure.
        logger = logging.getLogger('kts46.rpc_server.simulator')
        storage = CouchDBStorage(self.cfg.get('couchdb', 'dbaddress'), projectName, str(jobId))

        model = Model(ModelParams())
        job = self.server[projectName]['j'+str(jobId)]
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

if __name__ == '__main__':
    cfg, logger = init()

    # Create and configure server.
    address = cfg.get('rpc-server', 'address')
    port = cfg.getint('rpc-server', 'port')
    server = SimpleXMLRPCServer( (address, port), allow_none = True )

    # Register functions.
    couchdbProxy = CouchDBProxy(cfg)
    server.register_function(hello)
    server.register_function(shutdown)
    server.register_instance(couchdbProxy)

    # Run server.
    logging.info('Serving...')
    server.serve_forever()
