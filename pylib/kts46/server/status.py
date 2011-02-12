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
from kts46.mongodb import Storage
from kts46.model.Model import Model

class StatusServer:
    "A server that enables view of simulation status."

    def __init__(self, cfg):
        self.storage = Storage(cfg.get('mongodb', 'host'))

    #def getJobsList(self, projectName):
    #    return self.storage[projectName].getJobsList()

    def getProjectStatus(self, projectName):
        jobs = self.storage[projectName].getJobs()
        r = [ ]
        for job in jobs:
            r.append({'name': job.name, 'done': job.progress['done'],
                      'totalSteps': job.progress['totalSteps'],
                      'project': projectName,
                      'fullStatistics': job.progress['fullStatistics'],
                      'basicStatistics': job.progress['basicStatistics'],
                      'idleTimes': job.progress['idleTimes'],
                      'throughput': job.progress['throughput'],
                      })
        # If project contains nothing - add dummy job to display project in interface.
        if len(r) == 0:
            r.append({'visible': False, 'project': projectName})
        return r

    def getProjectStatus2(self, projectName):
        db = self.storage.server[projectName]
        # Go directly for statistics and believe that they are true.
        fields = ['name', 'done', 'totalSteps', 'basicStatistics', 'idleTimes',
                  'fullStatistics', 'throughput']
        ps = db.progresses.find({}, fields)
        r = []
        for a in ps:
            a['project'] = projectName
            if 'name' not in a: a['name'] = a['_id']
            r.append(a)

        # If project contains nothing - add dummy job to display project in interface.
        if len(r) == 0:
            r.append({'visible': False, 'project': projectName})
        return r

    def getServerStatus(self):
        projects = self.storage.getProjectNames()
        results = []
        for project in projects:
            results.extend(self.getProjectStatus2(project))
        return results

    def getJobStatistics(self, projectName, jobName, includeIdleTimes=False):
        """Returns job statistics dictionary. It is always dictionary and if
        statistics hasn't been already calculated it fields will be set to None."""
        project = self.storage[projectName]
        job = project[jobName]
        d = dict(job.statistics)
        # Remove utility fields of databases.
        if '_id' in d: del d['_id']
        if '_rev' in d: del d['_rev']
        # Remove cars idle times if required
        if not includeIdleTimes:
            d['idleTimes']['values'] = None
        return d
        
    def getModelDescription(self, projectName, jobName):
        project = self.storage[projectName]
        job = project[jobName]
        return job.definition

        
        