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

import couchdb, logging
from . import *
from SimulationProject import SimulationProject

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
            if PROJECT_DOCID in db:
                return True
        return False

    def __delitem__(self, key):
        """Deletes project with specified name if it exists. Otherwise raises
        KeyError."""
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
