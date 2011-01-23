# Copyright 2010-2011 Anthony Kolesov
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
import math
import numpy
import yaml

class StatisticsServer:
    "Class to calculate model simulation statistics."

    def __init__(self, cfg):
        self.cfg = cfg
        self.log = logging.getLogger(cfg.get('loggers', 'StatisticsServer'))

        
    def calculate(self, job):
        addCarData = job.db.cars.find({'job':job.name, 'state': 'add'},['carid','time'])
        delCarData = job.db.cars.find({'job':job.name, 'state': 'del'},['carid','time'])

        addCarTimes = dict((x['carid'], x['time']) for x in addCarData)
        delCarTimes = dict((x['carid'], x['time']) for x in delCarData)

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
        job.statistics['average'] = round(av if not math.isnan(av) else - 1, 4)
        job.statistics['stdeviation'] = round(stdd, 4)
        job.statistics['averageSpeed'] = round(avgSpeed, 4)
        job.statistics['finished'] = True
        
        if self.cfg.getboolean("worker", "calculateIdleTimes"):
            self.calculateIdleTimes(job)
        if self.cfg.getboolean('worker', "calculateThroughput"):
            self.calculateThroughput(job)
        
        job.save()


    def calculateIdleTimes(self, job):
        # Get cars ids. We need no repeatings.
        carsSpec = {'job': job.name, 'state': 'del'}
        cars = job.db.cars.find(carsSpec, ['carid']).distinct("carid")
        # distinct is useless for its original purpose because car can be
        # added or delete only once. But it used because it returns values
        # not documents. So I give that work to library and don't extract
        # them by myself.  
        
        # Initialize results.
        results = {}
        resultValues = []
        
        # Retrieve data for each car separately. 
        for carId in cars:
            # Get positions already sorted by time.
            spec = {'job': job.name, 'carid': carId}
            fields = ['time', 'pos', 'state']
            positions = job.db.cars.find(spec, fields).sort("time")
                    
            # Calculate idle time.
            idleTime = 0.0
            prevPos = None
            for pos in positions:
                if prevPos is not None and pos['pos'] == prevPos['pos']:
                    idleTime += pos['time'] - prevPos['time']
                prevPos = pos
            
            results[carId] = round(idleTime, 4)
            resultValues.append(idleTime)
            
            self.log.debug("Calculated idle time for car: %s", carId)
                
        # Calculate mean.
        mean = numpy.average(numpy.array(resultValues))
        
        # Store results
        d = {'values': results, 'average': round(mean, 4)}
        job.statistics['idleTimes'] = d
    
    def calculateThroughput(self, job):
        self.log.info("Calculating throughput.")
        points = ['start', 'end']
        result = []
        # Here we need .distinct because no 'del' or 'add' is used.
        cars = job.db.cars.find({'job': job.name}, ['carid']).distinct("carid")
        #carQuery = job.db.cars.find({'job': job.name}, ['carid'])
        #cars = set( map(lambda x: x['carid'], carQuery ) )
        self.log.info("Has to find throughput with %i cars", len(cars))
        for point in points:
            if point == 'start' or point == 'end':
                carsAmount = self.calculateEndpointsThroughput(job, point)
            else:
                posSpec = {'job': job.name, 'pos': {'$gte': point}}
                cursor = job.db.cars.find(posSpec, ['carid'])
                carsAmount = len(cursor.distinct("carid"))
                ##-
                #self.log.info("Calculating point %g by local method", point)
                #for carid in cars:
                #    posspec = {'job':job.name,'carid':carid,'pos':{'$gte':point}}
                #    # first: position ASC, then time DESC
                #    sort = [('pos', 1), ('time', -1)]
                #    carPosition = job.db.cars.find_one(posspec, sort=sort)
                #    # We can do something with time, but not now.
                #    if carPosition is not None:
                #        carsAmount += 1
                #self.log.info("Point %g finished by local method", point)
            throughput = float(carsAmount) / job.simulationParameters['duration'] * 3600
            result.append({'cars': carsAmount, 'rate': job.round(throughput),
                           'pos': point})
        job.statistics['throughput'] = result
        self.log.info("Throughput calculated for %i points.", len(points))
        
    def calculateEndpointsThroughput(self, job, point):
        """Calculates throughput for start and end points. That is much
        faster than for usual points because of 'state' field and indexes."""
        carState = 'add' if point == 'start' else 'del'
        return job.db.cars.find({'job': job.name, 'state': carState}, []).count()
        