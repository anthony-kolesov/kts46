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
from multiprocessing.managers import BaseManager

sys.path.append('../lib/')
from kts46 import CouchDBViewDefinitions
from kts46.serverApi import RPCServerException
from kts46.CouchDBStorage import CouchDBStorage


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


# Dummy class to represent scheduler
class Scheduler(BaseManager): pass
Scheduler.register('runJob')

class CouchDBProxy:

    def __init__(self, cfg):
        self.cfg = cfg
        self.logger = logging.getLogger('kts46.rpc_server.couchdb')
        self.storage = CouchDBStorage(cfg.get('couchdb', 'dbaddress'))


    def getNewJobId(self, projectName):
        """Creates new job id.

        It is guaranteed that there will be no dublicates, because after
        generation new id is written to database and CouchDB will not allow two
        same job ids because of revision number conflicts.
        RPCServerException is thrown if
        doesn't exist."""

        return self.storage[projectName].getNewJobId()


    def createProject(self, projectName):
        """Create in database project with specified name.

        An exception will be raised it project already exists.
        Arguments:
            projectName -- name of peoject to create."""
        self.storage.createProject(projectName)


    def projectExists(self, projectName):
        "Checks whether project with specified name already exists."
        return projectName in self.storage


    def deleteProject(self, projectName):
        """Deletes project with specified name if it exists. Otherwise raises
        RPCServerException."""
        del self.storage[projectName]


    def addJob(self, projectName, jobName, definition):
        """Adds specified job to project.

        RPCServerException will be raised if project doesn't exist or job with
        specified name already exists.
        Arguments:
            projectName -- name of model project.
            jobName -- job name.
            definition -- definition of job written in YAML.
        """
        self.storage[projectName].addJob(jobName, definition)


    def jobExists(self, projectName, jobName):
        """Checks whether job with provided name exists in project.

        RPCServerExceptpion is thrown if project doesn't exist."""
        return jobName in self.storage[projectName]


    def deleteJob(self, projectName, jobName):
        "Deletes job with specified name if it exists. Otherwise throws RPCServerException."
        p = self.storage[projectName]
        del p[jobName]

    def runJob(self, projectName, jobName):
        "Runs simulation job, using remote scheduler."

        if not self.jobExists(projectName, jobName):
            msg = "Couldn't run job %s of project %s that doesn't exist."
            raise RPCServerException(msg % (jobName, projectName))

        schedulerAddress = (self.cfg.get('scheduler', 'address'),
                            self.cfg.getint('scheduler', 'port') )
        scheduler = Scheduler(address=schedulerAddress,
                              authkey=self.cfg.get('scheduler', 'authkey'))
        scheduler.connect()
        self.logger.info('Running job: %s.%s' % (projectName, jobName))
        scheduler.runJob(projectName, jobName)


if __name__ == '__main__':
    cfg, logger = init()

    # Create and configure server.
    address = cfg.get('rpc-server', 'address')
    port = cfg.getint('rpc-server', 'port')
    server = SimpleXMLRPCServer( (address, port), allow_none = True )

    # Register functions.
    couchdbProxy = CouchDBProxy(cfg)
    server.register_function(hello)
    server.register_instance(couchdbProxy)

    # Run server.
    logging.info('Serving...')
    server.serve_forever()
