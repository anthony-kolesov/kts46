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
        
        if self.cfg.getboolean("worker", "calculateStops"):
            self.calculateStops(job)
        
        job.save()


    def calculateStops(self, job):
        # Get cars indexes.
        #carsNotUniqueView = job.project.db.view("basicStats/cars")[job.id]
        carsUnique = job.db.cars.find({'job': job.name},['carid']).distinct("carid")
        
        # Filter from cars that haven't finished distance.
        #carsNotUnique = []
        #deletedCars = []
        #for it in carsNotUniqueView:
        #    v = it['value']
        #    if len(v) > 1 and v[1] == 'del':
        #        deletedCars.append(v[0])
        #    else:
        #        carsNotUnique.append(v[0]) 
        
        #cars = numpy.unique(filter(lambda x: x in deletedCars, carsNotUnique))
        cars = carsUnique
        
        results = {}
        resultValues = []
        
        for carId in cars:
            # Get positions.
            #positionsView = job.project.db.view("basicStats/carPositions")
            positionsView = job.db.cars.find({'job':job.name, 'carid': carId},
                                        ['time', 'pos', 'state']).sort("time")
            #positionsView = positionsView[ [job.id, carId] ]
            # Convert them to python list.
            #positions = [ it['value'] for it in positionsView ]
            positions = positionsView
            # Sort them by time.
            #positions.sort(key = lambda a: a['time'])
                    
            # Calculate stand-still time.
            standTime = 0.0
            prevPos = None
            wasDeleted = False
            for pos in positions:
                if prevPos is not None and pos['pos'] == prevPos['pos']:
                    standTime += pos['time'] - prevPos['time']
                if 'state' in pos and pos['state'] == 'del':
                    wasDeleted = True
                prevPos = pos
            
            if wasDeleted:    
                results[carId] = round(standTime, 4)
                resultValues.append(standTime)
                
                #job.save()
                self.log.info("Calculated stops for car: %s", carId)
            else:
                self.log.info("Skip cars %s stall idle times: dodn't finished road.", carId)
                
        
        # Store results
        #d = {'values': results, 'average': None, 'stdev': None}
        #job.statistics['stallTimes'] = d
        
        # Calculate mean and standard deviation.
        resultValues = numpy.array(resultValues)
        mean = numpy.average(resultValues)
        stdev = numpy.std(resultValues) 
        
        # Store results
        d = {'values': results, 'average': round(mean, 4), 'stdev': round(stdev, 4)}
        job.statistics['stallTimes'] = d
            

    #def calculate(self, job):
    #    view = job.project.db.view('_all_docs', {'include_docs': True})
    #    startkey = 's' + job.id
    #    endkey = 's' + (job.id + 1)
    #    for state in view[startkey:endkey]:
            