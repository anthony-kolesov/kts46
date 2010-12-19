"""
Provides database server that is able to manage projects and jobs in the
database.

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

import sys, logging
# Project imports.
sys.path.append('../../../lib/')
from kts46.CouchDBStorage import CouchDBStorage


class DatabaseServer:

    def __init__(self, cfg):
        self._cfg = cfg
        self._log = logging.getLogger(cfg.get('loggers', 'DatabaseServer'))
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
    #
    #def runJob(self, projectName, jobName):
    #    "Runs simulation job, using remote scheduler."
    #
    #    if not self.jobExists(projectName, jobName):
    #        msg = "Couldn't run job %s of project %s that doesn't exist."
    #        raise RPCServerException(msg % (jobName, projectName))
    #
    #    schedulerAddress = (self.cfg.get('scheduler', 'address'),
    #                        self.cfg.getint('scheduler', 'port') )
    #    scheduler = Scheduler(address=schedulerAddress,
    #                          authkey=self.cfg.get('scheduler', 'authkey'))
    #    scheduler.connect()
    #    self.logger.info('Running job: %s.%s' % (projectName, jobName))
    #    scheduler.runJob(projectName, jobName)
