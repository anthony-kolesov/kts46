# Copyright 2010-2011 Anthony Kolesov
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json, sys
import logging
import math
import random
from datetime import timedelta

import kts46.utils
from Car import Car
from Road import Road
from TrafficLight import SimpleSemaphore
from Endpoint import Endpoint
from Crossroad import Crossroad


class Model(object):
    "Defines a model that can simulate road traffic."

    defaultParams = {'inputRate': 1200,
        'safeDistance': 20, 'safeDistanceRear': 10, 'trafficLightStopDistance': 5,
        "accelerationLimit": 2.0, # m / s^2 for (13.5 s to 100 kmph)
        "brakingLimit": 6.5, # m / s^2 (like 21 m from 60 kmph)
        "comfortBrakingLimit": 4.5, # m / s^2
        "driverReactionTime": 0.8, # s
        "minimalDistance": 3, # m
        "speed": [10, 20], # m/s
        "lineChangingDelay": 1.0 # m/s
    }

    def __init__(self, params):
        """Initializes new model with provided set of parameters.

        :param params: Model parameters.
        :type params: dictionary"""
        self.time = timedelta()
        #self._cars = []
        #self._enterQueue = []
        self._lights = []
        self.roads = {}
        self._lastCarGenerationTime = timedelta()
        self.params = params
        self._loggerName = 'kts46.roadModel'
        self._logger = logging.getLogger(self._loggerName)
        self._lastCarId = -1

        # New
        self._endpoints = {}
        self.crossroads = {}
        self.view = {}
        self.simulationParameters = {}


    def run_step(self, milliseconds):
        stopDistance = self.params['safeDistance']
        timeStep = timedelta(milliseconds=milliseconds)
        newTime = self.time + timeStep

        # Add cars to enter points
        self.generateCars(newTime)

        # Move cars from enter points to roads
        self.addCarsFromEndpointsToRoad()

        # Move cars (change temporary variable)
        for road in self.roads.itervalues():
            toRemove = [ ]
            for car in road.cars:
                if car.state != Car.DELETED:
                    car.prepareMove(timeStep)
                else:
                    toRemove.append(car)
            for car in toRemove: road.cars.remove(car)

        # Finalize movement of cars
        for road in self.roads.itervalues():
            for car in road.cars:
                car.finishMove()

        self.time = newTime


    def addCarsFromEndpointsToRoad(self):
        for endpointId in self._endpoints:
            endpoint = self._endpoints[endpointId]
            self.addCarsFromQueueToRoad(endpoint)


    def addCarsFromQueueToRoad(self, endpoint):
        "Add cars from entering queue to road."
        # If there is a car in the queue, then send it.
        # Try to add cars while there was at least one succesfull added.
        addCar = True
        while len(endpoint.enterQueue) > 0 and addCar:
            # Start with generated line and if it is busy try others.
            addCar = False
            car = endpoint.enterQueue[0]
            if self.canAddCar(endpoint, car.line):
               addCar = True
            else:
                # This algorithms favorites first lines.
                # I consider this correct for most cases.
                for i in range(0, endpoint.road.lines[endpoint.direction] ):
                    if i != car.line and self.canAddCar(endpoint, i):
                        car.line = i
                        addCar = True
                        break
            if addCar:
                endpoint.road.cars.append(car)
                car.state = Car.ADDED
                del endpoint.enterQueue[0]


    def generateCars(self, newTime):
        "Generate new cars at endpoints."
        for endpointId, endpoint in self._endpoints.iteritems():
            carGenRate = timedelta(seconds=3600/endpoint.inputRate)

            # How many
            carsToGenerate = 0
            while (endpoint.lastGenerationTime + carGenRate) <= newTime:
                carsToGenerate += 1
                endpoint.lastGenerationTime += carGenRate

            # Add
            speedMultiplier = self.params['speed'][1] - self.params['speed'][0]
            speedAdder = self.params['speed'][0]
            for i in xrange(carsToGenerate):
                speed = math.floor(random.random() * speedMultiplier) + speedAdder
                self._lastCarId += 1
                line = math.floor(random.random() * endpoint.road.getLinesForPoint(endpointId))
                newCar = Car(model=self, road=endpoint.road, id=self._lastCarId, speed=speed, line=line)
                newCar.direction = endpoint.direction
                self._logger.debug('Created car: [speed: %f].', speed)
                endpoint.enterQueue.append(newCar)
                


    def getNearestTrafficLight(self, position, direction, line=0):
        "Get nearest traffic light to specified position in forward destination."
        return self.getNearestObjectInArray(self._lights, position, direction, line)

    def getNearestCar(self, road, position, direction, line=0):
        """Get nearest car to specified position in forward destination.
        If there is no leading car, then ``None`` will be returned."""
        #return self.getNearestObjectInArray(road.cars, position, direction, line)
        nextCar = road.getNearestCar(position, direction, line)
        distance = 0

        targetEndpoint = road.getNextEndpoint(direction)
        while nextCar is None and isinstance(targetEndpoint[0], Crossroad):
            oppositeRoad = targetEndpoint[0].roads[ (targetEndpoint[1] + 2) % 4 ]
            if oppositeRoad is not None:
                distance += road.length
                road = oppositeRoad
                
                if targetEndpoint[0] is road.points[0]:
                    direction = 0
                else:
                    direction = 1
                
                nextCar = road.getNearestCar(0, direction, line)
                targetEndpoint = road.getNextEndpoint(direction)
            else:
                break

        if nextCar is not None:
            return (nextCar, nextCar.position - position - nextCar.length + distance)
        else:
            return None


    def getNearestObjectInArray(self, array, position, direction, line=0):
        "Get nearest object in array to specified position in forward destination."
        position += 0.1
        current = None
        current_pos = -1.0 # just to make sure :)
        for i in array:

            if hasattr(i, 'direction') and i.direction != direction:
                continue

            # Check if it is in our line and skip it if not.
            # Objects that has not line attribute affect all lines,
            # like traffic lights.
            if hasattr(i, "line") and i.line != line:
                continue

            # Deleted cars already doesn't exists.
            if isinstance(i, Car) and hasattr(i, "state") and i.state == Car.DELETED:
                continue

            pos = i.position
            # >= is very important so car won't try to go through another car.
            if pos >= position and ((current is None) or current_pos > pos):
                current = i
                current_pos = pos
        return current


    def getFollowingCar(self, road, position, direction, line=0):
        """Get nearest following car to specified position in backward destination.
        If there is no following car, then ``None`` will be returned."""
        return self.getFollowingObjectInArray(road.cars, position, direction, line)


    def getFollowingObjectInArray(self, array, road, position, direction, line=0):
        "Get nearest object in array to specified position in backward destination."
        current = None
        current_pos = -1.0 # just to make sure :)
        for i in array:

            if hasattr(i, 'direction') and i.direction != direction:
                continue

            # Check if it is in our line and skip it if not.
            # Objects that has not line attribute affect all lines,
            # like traffic lights.
            if hasattr(i, "line") and i.line != line:
                continue

            # Deleted cars already doesn't exists.
            if isinstance(i, Car) and hasattr(i, "state") and i.state == Car.DELETED:
                continue

            pos = i.position
            if pos <= position and ((current is None) or current_pos < pos):
                current = i
                current_pos = pos
        return current

    def canAddCar(self, endpoint, line=0):
        "Defines whether car can be added to specified line."
        lastCar = self.getNearestCar(endpoint.road, 0.0, endpoint.direction, line)
        #return lastCar is None or lastCar.position - lastCar.length > self.params['safeDistance']
        return lastCar is None or lastCar[1] > self.params['safeDistance']


    def getStateData(self):
        """Returns object data that represents current state of a model."""
        data = {}
        # Traffic lights
        lights = {}
        for light in self._lights:
            lights[light.id] = light.getStateData()
        data['trafficLights'] = lights

        # Cars
        cars = {}
        for road in self.roads:
            for car in self.roads[road].cars:
                cars[car.id] = car.getStateData()
                cars[car.id].update(car.getDescriptionData())
        data['cars'] = cars

        # Enter queue
        #enterQueue = []
        #for car in self._enterQueue:
        #    enterQueue.append(car.getStateData())
        #    enterQueue[-1].update(car.getDescriptionData())
        #data['enterQueue'] = enterQueue

        # Fields
        data['time'] = kts46.utils.timedelta2str(self.time)
        data['lastCarGenerationTime'] = kts46.utils.timedelta2str(self._lastCarGenerationTime)
        data['lastCarId'] = self._lastCarId

        # Endpoints
        data['endpoints'] = dict( (endpointId, endpoint.getDescriptionData()) for endpointId, endpoint in self._endpoints.iteritems())

        # Result.
        return data


    def getDescriptionData(self):
        "Gets dictionary describing model."
        data = {}
        data['modelParameters'] = self.params
        lights = {}
        for light in self._lights:
            lights[light.id] = light.getDescriptionData()
        data['trafficLights'] = lights
        if self._road is not None:
            data['road'] = self._road.getDescriptionData()
        return data


    def load(self, description):
        self.params = dict(Model.defaultParams)
        self.params.update(description['modelParameters'])
        self.simulationParameters = description['simulationParameters']
        self.view = description['view']
        for endpointId, endpointData in description['endpoints'].iteritems():
            if 'inputRate' not in endpointData:
                endpointData['inputRate'] = self.params['inputRate']
            self._endpoints[endpointId] = Endpoint(name=endpointId, **endpointData)
        for crossroadId, crossroadData in description['crossroads'].iteritems():
            self.crossroads[crossroadId] = Crossroad(name=crossroadId, **crossroadData)
        for roadId, roadData in description['roads'].iteritems():
            #roadData['points'][0] = self.getPoint(roadData['points'][0][0])
            #roadData['points'][1] = self.getPoint(roadData['points'][1][0])
            self.roads[roadId] = Road(roadId, self, **roadData)

    def getPoint(self, pointName):
        if pointName in self._endpoints:
            return self._endpoints[pointName]
        return self.crossroads[pointName]
