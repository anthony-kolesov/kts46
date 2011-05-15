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
        self._cars = []
        self._enterQueue = []
        self._lights = []
        self._road = Road()
        self._lastCarGenerationTime = timedelta()
        self.params = params
        self._loggerName = 'kts46.roadModel'
        self._logger = logging.getLogger(self._loggerName)
        self._lastCarId = -1


    def run_step(self, milliseconds):
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


    def addCarsFromQueueToRoad(self):
        "Add cars from entering queue to road."
        # If there is a car in the queue, then send it.
        # Try to add cars while there was at least one succesfull added.
        addCar = True
        while len(self._enterQueue) > 0 and addCar:
            # Start with generated line and if it is busy try others.
            addCar = False
            if self.canAddCar(self._enterQueue[0].line):
               addCar = True
            else:
                # This algorithms favorites first lines. That is considered
                # logical in most cases.
                for i in range(0, self._road.lines):
                    if self.canAddCar(i):
                        self._enterQueue[0].line = i
                        addCar = True
                        break
            if addCar:
                self._addCar(self._enterQueue[0])
                del self._enterQueue[0]


    def addCars(self, amount):
        """Add cars to entering queue.

        :param amount: Amount of cars to add to queue.
        :type amount: int"""
        speedMultiplier = self.params['speed'][1] - self.params['speed'][0]
        speedAdder = self.params['speed'][0]
        for i in xrange(amount):
            speed = math.floor(random.random() * speedMultiplier) + speedAdder
            self._lastCarId += 1
            line = math.floor(random.random() * self._road.lines)
            newCar = Car(model=self, road=self._road, id=self._lastCarId, speed=speed, line=line)
            self._logger.debug('Created car: [speed: %f].', speed)
            self._enterQueue.append(newCar)


    def howManyCarsToAdd(self, newTime):
        "Define how many cars can be added to the model."
        newCarGenRate = timedelta(seconds=3600/self.params['inputRate'])
        lastCarTime = self._lastCarGenerationTime
        carsToGenerate = 0
        while lastCarTime <= newTime:
            carsToGenerate += 1
            lastCarTime += newCarGenRate
        return (carsToGenerate, lastCarTime)


    def getNearestTrafficLight(self, position):
        "Get nearest traffic light to specified position in forward destination."
        return self.getNearestObjectInArray(self._lights, position)

    def getNearestCar(self, position, line=0):
        """Get nearest car to specified position in forward destination.
        If there is no leading car, then ``None`` will be returned."""
        return self.getNearestObjectInArray(self._cars, position, line)

    def getNearestObjectInArray(self, array, position, line=0):
        "Get nearest object in array to specified position in forward destination."
        position += 0.1
        current = None
        current_pos = -1.0 # just to make sure :)
        for i in array:

            # Check if it is in our line and skip it if not.
            # Objects that has not line attribute affect all lines,
            # like traffic lights.
            if hasattr(i, "line") and i.line != line:
                continue

            # Deleted cars already doesn't exists.
            if hasattr(i, "state") and i.state == Car.DELETED:
                continue

            pos = i.position
            #if hasattr(i, "length"):
            #    pos -= i.length
            # >= is very important so car won't try to go through another car.
            if pos >= position and ((current is None) or current_pos > pos):
                current = i
                current_pos = pos
        return current


    def getFollowingCar(self, position, line=0):
        """Get nearest following car to specified position in backward destination.
        If there is no following car, then ``None`` will be returned."""
        return self.getFollowingObjectInArray(self._cars, position, line)


    def getFollowingObjectInArray(self, array, position, line=0):
        "Get nearest object in array to specified position in backward destination."
        current = None
        current_pos = -1.0 # just to make sure :)
        for i in array:

            # Check if it is in our line and skip it if not.
            # Objects that has not line attribute affect all lines,
            # like traffic lights.
            if hasattr(i, "line") and i.line != line:
                continue

            # Deleted cars already doesn't exists.
            if hasattr(i, "state") and i.state == Car.DELETED:
                continue

            pos = i.position
            if pos <= position and ((current is None) or current_pos < pos):
                current = i
                current_pos = pos
        return current

    def canAddCar(self, line=0):
        "Defines whether car can be added to specified line."
        lastCar = self.getNearestCar(-100.0, line) # Detect cars which are comming on the road.
        return lastCar is None or lastCar.position - lastCar.length > self.params['safeDistance']

    def _addCar(self, car):
        "Add car to the model, but not to the road."
        self._cars.append(car)
        car.state = Car.ADDED

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
        for car in self._cars:
            cars[car.id] = car.getStateData()
            cars[car.id].update(car.getDescriptionData())
        data['cars'] = cars

        # Enter queue
        enterQueue = []
        for car in self._enterQueue:
            enterQueue.append(car.getStateData())
            enterQueue[-1].update(car.getDescriptionData())
        data['enterQueue'] = enterQueue

        # Fields
        data['time'] = kts46.utils.timedelta2str(self.time)
        data['lastCarGenerationTime'] = kts46.utils.timedelta2str(self._lastCarGenerationTime)
        data['lastCarId'] = self._lastCarId

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
