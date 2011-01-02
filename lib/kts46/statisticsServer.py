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

import json, math, numpy, logging
from urllib2 import urlopen

class StatisticsServer:

    def __init__(self, cfg):
        self.cfg = cfg
        self.log = logging.getLogger(cfg.get('loggers', 'StatisticsServer'))

    def _getJSON(self, url):
        a = urlopen(url)
        text = a.read(None).decode("UTF-8", "strict")
        a.close()
        return json.loads(text)

    def calculate(self, project, job):

        addCarPath = self.cfg.get("couchdb", "addCarView").format(
            project=project, job=job.id, nextjob=job.id + 1)
        delCarPath = self.cfg.get("couchdb", "deleteCarView").format(
            project=project, job=job.id, nextjob=job.id + 1)

        self.log.info('GET: ' + addCarPath)
        self.log.info('GET: ' + delCarPath)

        # Connect to CouchDB and get data.
        addCarData = self._getJSON(addCarPath)
        delCarData = self._getJSON(delCarPath)

        addCarTimes = dict((x['key'][1], x['value']['time']) for x in addCarData['rows'])
        delCarTimes = dict((x['key'][1], x['value']['time']) for x in delCarData['rows'])

        times = {}
        moveTimes = []
        for carid, addTime in addCarTimes.items():
            if carid in delCarTimes:
                times[carid] = {'add': addTime, 'del': delCarTimes[carid]}
                moveTimes.append(delCarTimes[carid] - addTime)

        # Create numpy array and count statistics.
        arr = numpy.array(moveTimes)
        av = numpy.average(arr)
        stdd = numpy.std(arr)
        self.log.info("Average: {0}".format(av))
        self.log.info("Standard deviation: {0}".format(stdd))
        job.statistics['average'] = av if not math.isnan(av) else - 1
        job.statistics['stdeviation'] = stdd
        job.statistics['finished'] = True
        job.save()
