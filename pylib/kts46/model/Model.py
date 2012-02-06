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

import json
import logging
import math
import random
from datetime import timedelta

import kts46.utils
from Car import Car
from Road import Road
from TrafficLight import SimpleSemaphore
from Endpoint import Endpoint


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
        self._roads = {}
        self._lastCarGenerationTime = timedelta()
        self.params = params
        self._loggerName = 'kts46.roadModel'
        self._logger = logging.getLogger(self._loggerName)
        self._lastCarId = -1

        # New
        self._endpoints = {}


    def run_step(self, milliseconds):
        stopDistance = self.params['safeDistance']
        timeStep = timedelta(milliseconds=milliseconds)
        newTime = self.time + timeStep

        # Add cars to enter points
        self.generateCars(newTime)

        # Move cars from enter points to roads
        self.addCarsFromEndpointsToRoad()

        # Move cars (change temporary variable)
        # Finalize movement of cars
        # Remove cars that reached endpoint

        self.time = newTime


    def run_step1(self, milliseconds):
        """Performs one step of simulation.

        :param milliseconds: length of step in milliseconds.
        :type milliseconds: int"""
        stopDistance = self.params['safeDistance']

        timeStep = timedelta(milliseconds=milliseconds)
        newTime = self.time + timeStep # Time after step is performed.

        for light in self._lights:
            if newTime > light.getNextSwitchTime():
                light.switch(newTime)

        toRemove = [ ]
        for car in self._cars:
            if car.state != Car.DELETED:
                car.prepareMove(timeStep)
            else:
                toRemove.append(car)

        for car in toRemove: self._cars.remove(car)
        for car in self._cars: car.finishMove()

        # Generate new car.
        # It is always added to the queue and if there is enough place then
        # it will be instantly added to the road.
        carsToAdd, newLastCarTime = self.howManyCarsToAdd(newTime)
        self.addCars(carsToAdd)
        self._lastCarGenerationTime = newLastCarTime

        self.addCarsFromQueueToRoad()

        # Update time.
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
                


    def getNearestTrafficLight(self, position):
        "Get nearest traffic light to specified position in forward destination."
        return self.getNearestObjectInArray(self._lights, position)

    def getNearestCar(self, road, position, direction, line=0):
        """Get nearest car to specified position in forward destination.
        If there is no leading car, then ``None`` will be returned."""
        return self.getNearestObjectInArray(road.cars, position, direction, line)

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
        return self.getFollowingObjectInArray(self._cars, position, line)


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
        lastCar = self.getNearestCar(endpoint.road, -100.0, endpoint.direction, line)
        return lastCar is None or lastCar.position - lastCar.length > self.params['safeDistance']


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
        for road in self._roads:
            for car in self._roads[road].cars:
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


    def load(self, description, state=None):
        self.params = description['modelParameters']
        for endpointId, endpointData in description['endpoints'].iteritems():
            if 'inputRate' not in endpointData:
                endpointData['inputRate'] = self.params['inputRate']
            self._endpoints[endpointId] = Endpoint(name=endpointId, **endpointData)
        for roadId, roadData in description['roads'].iteritems():
            roadData['points'][0] = self._endpoints[ roadData['points'][0][0] ]
            roadData['points'][1] = self._endpoints[ roadData['points'][1][0] ]
            self._roads[roadId] = Road(name=roadId, **roadData)


    def load1(self, description, state=None):
        "Loads object from JSON data."

        self.params = description['modelParameters']
        self._road.load(description['road'])

        for lightId, lightData in description['trafficLights'].iteritems():
            light = SimpleSemaphore(id=lightId)
            lState = {}
            if state is not None:
                lState = state['trafficLights'][lightId]
            light.load(lightData, lState)
            self._lights.append(light)

        if state is not None:
            for carData in state['cars'].itervalues():
                c = Car(model=self, road=self._road)
                c.load(carData, carData)
                self._cars.append(c)

            for carData in state['enterQueue']:
                c = Car(model=self, road=self._road)
                c.load(carData, carData)
                self._enterQueue.append(c)

            # Fields
            self.time = kts46.utils.str2timedelta(state['time'])
            self._lastCarGenerationTime = kts46.utils.str2timedelta(state['lastCarGenerationTime'])
            self._lastCarId = state['lastCarId']
