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

import logging
from kts46.db.CouchDBStorage import CouchDBStorage

class StatusServer:
    "A server that enables view of simulation status."

    def __init__(self, cfg):
        self.storage = CouchDBStorage(cfg.get('couchdb', 'dbaddress'))

    def getJobStatus(self, projectName, jobName):
        project = self.storage[projectName]
        job = project[jobName]
        progress = job.progress
        progressPcnt = progress['done'] / progress['totalSteps']
        msg = "{proj}.{job}: {progress} ({done}/{total}).".format(proj=projectName, job=jobName,
            progress=progressPcnt, done=progress['done'], total=progress['totalSteps'])
        return msg

    def getJobsList(self, projectName):
        return self.storage[projectName].getJobsList()

    def getProjectStatus(self, projectName):
        jobs = self.storage[projectName].getJobs()
        r = [ ]
        for job in jobs:
            r.append({'name': job.name, 'done': job.progress['done'],
                      'total': job.progress['totalSteps'],
                      'project': projectName})
        # If project contains nothing - add dummy job to display project in interface.
        if len(r) == 0:
            r.append({'visible': False, 'project': projectName})
        return r

    def getServerStatus(self):
        projects = self.storage.getProjects()
        results = []
        for project in projects:
            results.extend(self.getProjectStatus(project))
        return results
