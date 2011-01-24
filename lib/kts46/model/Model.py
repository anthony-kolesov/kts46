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

import random
import json
import math
import logging
import yaml

from datetime import timedelta

from Car import Car
from Road import Road
from TrafficLight import SimpleSemaphore


class ModelParams:
    """Defines simulation parameters such as min and max speed, safe distance
    between vehicles and interval between generations of new cars."""

    def __init__(self):
        self.carGenerationInterval = 3.0
        self.safeDistance = 5.0
        self.maxSpeed = 20.0
        self.minSpeed = 10.0


class Model(object):

    def __init__(self, params):
        self.time = timedelta()
        self._cars = []
        self._enterQueue = []
        self._lastSendCars = {}
        self._lights = []
        self._road = None
        self._lastCarGenerationTime = timedelta()
        self.params = params
        self._loggerName = 'kts46.roadModel'
        self._logger = logging.getLogger(self._loggerName)
        self._lastCarId = -1

    def run_step(self, milliseconds):
        stopDistance = self.params.safeDistance

        timeStep = timedelta(milliseconds=milliseconds)
        newTime = self.time + timeStep # Time after step is performed.

        for light in self._lights:
            if newTime > light.getNextSwitchTime():
                light.switch(newTime)

        toRemove = [ ]
        for car in self._cars:
            if car.state != Car.DELETED:
                # Update state.
                if car.state == Car.ADDED: car.state = Car.ACTIVE

                distanceToMove = car.get_speed() * timeStep.seconds
                distanceToMove += car.get_speed() * timeStep.microseconds * 1e-6
                distanceToMove += car.get_speed() * timeStep.days * 86400 # 3600 * 24

                # Check for red traffic light.
                nearestTL = self.get_nearest_traffic_light(car.get_position())
                if nearestTL is not None and not nearestTL.is_green():
                    if nearestTL.get_position() - car.get_position() - stopDistance < distanceToMove:
                        distanceToMove = nearestTL.get_position() - car.get_position() - stopDistance
                        if distanceToMove < 0:
                            distanceToMove = 0.0

                # Check for leading car.
                nearestCar = self.get_nearest_car(car.get_position(), car.line)
                if nearestCar is not None:
                    nearestCarBack = nearestCar.get_position() - nearestCar.get_length()
                    possiblePosition = nearestCarBack - stopDistance
                    if possiblePosition - car.get_position() < distanceToMove:
                        distanceToMove = possiblePosition - car.get_position()
                        if distanceToMove < 0:
                            distanceToMove = 0.0

                car.move(distanceToMove)
                if self._road.length < car.get_position():
                    car.state = Car.DELETED
            else:
                toRemove.append(car)

        for car in toRemove: self._cars.remove(car)

        # Generate new car.
        # It is always added to the queue and if there is enough place then
        # it will be instantly added to the road.
        carsToAdd, newLastCarTime = self.howMuchCarsToAdd(newTime)
        self.addCars(carsToAdd)
        self._lastCarGenerationTime = newLastCarTime

        self.addCarsFromQueueToRoad()

        # Update time.
        self.time = newTime


    def addCarsFromQueueToRoad(self):
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
        speedMultiplier = self.params.maxSpeed - self.params.minSpeed
        speedAdder = self.params.minSpeed
        for i in xrange(amount):
            speed = math.floor(random.random() * speedMultiplier) + speedAdder
            self._lastCarId += 1
            line = math.floor(random.random() * self._road.lines)
            newCar = Car(id=self._lastCarId, speed=speed, line=line)
            self._logger.debug('Created car: [speed: %f].', speed)
            self._enterQueue.append(newCar)


    def howMuchCarsToAdd(self, newTime):
        newCarGenRate = self.params.carGenerationInterval
        lastCarTime = self._lastCarGenerationTime
        carsToGenerate = 0
        while lastCarTime <= newTime:
            carsToGenerate += 1
            lastCarTime += newCarGenRate
        return (carsToGenerate, lastCarTime)


    def get_nearest_traffic_light(self, position):
        return self.get_nearest_object_in_array(self._lights, position)

    def get_nearest_car(self, position, line=0):
        return self.get_nearest_object_in_array(self._cars, position, line)

    def get_nearest_object_in_array(self, array, position, line=0):
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

            pos = i.get_position()
            if hasattr(i, "get_length"):
                pos -= i.get_length()
            if pos > position and ((current is None) or current_pos > pos):
                current = i
                current_pos = pos
        return current

    def canAddCar(self, line=0):
        lastCar = self.get_nearest_car(-100.0, line) # Detect cars which are comming on the road.
        return lastCar is None or lastCar.get_position() - lastCar.get_length() > self.params.safeDistance

    def _addCar(self, car):
        self._cars.append(car)
        car.state = Car.ADDED

    def get_state_data(self):
        """Returns object data that represents current state of a model."""
        # Traffic lights
        lights = {}
        for light in self._lights:
            lights[light.get_id()] = light.get_state_data()
        # Cars
        cars = {}
        for car in self._cars:
            cars[car.get_id()] = car.get_state_data()
        # Result.
        return {'cars': cars, 'lights': lights}

    def get_description_data(self):
        data = {}
        data['lights'] = {}
        for light in self._lights:
            data['lights'][light.get_id()] = light.get_description_data()
        if self._road is not None:
            data['road'] = self._road.getDescriptionData()
        return json.dumps(data)

    def loadYAML(self, yamlData):
        objData = yaml.safe_load(yamlData)
        # fields
        if "carGenerationInterval" in objData:
            self.params.carGenerationInterval = \
                timedelta(seconds=objData["carGenerationInterval"])
            self.params.inputRate = 3600 / objData["carGenerationInterval"]
        if "inputRate" in objData:
            inputRate = objData["inputRate"]
            # Store both but inputRate is used for storage while
            # carGenerationInterval is used in model.
            self.params.inputRate = inputRate
            self.params.carGenerationInterval = timedelta(seconds=3600/inputRate)
        if "safeDistance" in objData:
           self.params.safeDistance = objData["safeDistance"]
        if "maxSpeed" in objData:
           self.params.maxSpeed = objData["maxSpeed"]
        if "minSpeed" in objData:
           self.params.minSpeed = objData["minSpeed"]
        # collections
        if "road" in objData:
            self._road = objData["road"]
        if "trafficLights" in objData:
            self._lights = objData["trafficLights"]
        if 'time' in objData: self.time = objData['time']
        if 'lastCarGenerationTime' in objData:
            self._lastCarGenerationTime = objData['lastCarGenerationTime']
        if 'lastCarId' in objData: self._lastCarId = objData['lastCarId']
        # cars, last send cars, enter queue
        if 'cars' in objData: self._cars = objData['cars']
        if 'lastSendCars' in objData: self._lastSendCars = objData['lastSendCars']
        if 'enterQueue' in objData: self._enterQueue = objData['enterQueue']


    def asYAML(self):
        d = {}
        d["inputRate"] = self.params.inputRate
        d["safeDistance"] = self.params.safeDistance
        d["maxSpeed"] = self.params.maxSpeed
        d["minSpeed"] = self.params.minSpeed
        d["road"] = self._road
        d["trafficLights"] = self._lights

        d['time'] = self.time
        d['cars'] = self._cars
        d['enterQueue'] = self._enterQueue
        d['lastSendCars'] = self._lastSendCars
        d['lastCarGenerationTime'] = self._lastCarGenerationTime
        d['lastCarId'] = self._lastCarId

        return yaml.dump(d)
