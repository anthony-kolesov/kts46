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

import json, math, numpy, logging
import yaml

class StatisticsServer:

    def __init__(self, cfg):
        self.cfg = cfg
        self.log = logging.getLogger(cfg.get('loggers', 'StatisticsServer'))

    def calculate(self, job):
        addCarData = job.project.db.view("basicStats/addCar")[job.id]
        delCarData = job.project.db.view("basicStats/deleteCar")[job.id]

        addCarTimes = dict((x['value']['car'], x['value']['time']) for x in addCarData)
        delCarTimes = dict((x['value']['car'], x['value']['time']) for x in delCarData)

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
        
        definition = yaml.safe_load(job.definition)
        avgSpeed = definition['road'].length / av
        
        self.log.info("Average: {0}".format(av))
        self.log.info("Standard deviation: {0}".format(stdd))
        job.statistics['average'] = av if not math.isnan(av) else - 1
        job.statistics['stdeviation'] = stdd
        job.statistics['averageSpeed'] = avgSpeed
        job.statistics['finished'] = True
        
        if self.cfg.getboolean("worker", "calculateStops"):
            self.calculateStops(job)
        
        job.save()

    def calculateStops(self, job):
        # Get cars indexes.
        carsNotUniqueView = job.project.db.view("basicStats/cars")[job.id]
        
        # Filter cars that haven't finished distance.
        carsNotUnique = []
        deletedCars = []
        for it in carsNotUniqueView:
            v = it['value']
            if len(v) > 1 and v[1] == 'del':
                deletedCars.append(v[0])
            else:
                carsNotUnique.append(v[0]) 
        
        cars = numpy.unique(filter(lambda x: x in deletedCars, carsNotUnique))
        
        results = {}
        resultValues = []
        
        for carId in cars:
            # Get positions.
            positionsView = job.project.db.view("basicStats/carPositions")
            positionsView = positionsView[ [job.id, carId] ]
            # Convert them to python list.
            positions = [ it['value'] for it in positionsView ]
            # Sort them by time.
            positions.sort(key = lambda a: a['time'])
            # Calculate stand-still time.
            standTime = 0.0
            for pos in xrange(1, len(positions) ):
                if positions[pos]['pos'] == positions[pos-1]['pos']:
                    standTime += positions[pos]['time'] - positions[pos-1]['time']
            results[carId] = standTime
            resultValues.append(standTime)
            
            # Store results
            d = {'values': results, 'average': None, 'stdev': None}
            job.statistics['stallTimes'] = d
            #job.save()
            self.log.info("Calculated stops for car: %s", carId)
            
        
        # Calculate mean and standard deviation.
        resultValues = numpy.array(resultValues)
        mean = numpy.average(resultValues)
        stdev = numpy.std(resultValues) 
        
        # Store results
        d = {'values': results, 'average': mean, 'stdev': stdev}
        job.statistics['stallTimes'] = d
            

    #def calculate(self, job):
    #    view = job.project.db.view('_all_docs', {'include_docs': True})
    #    startkey = 's' + job.id
    #    endkey = 's' + (job.id + 1)
    #    for state in view[startkey:endkey]:
            