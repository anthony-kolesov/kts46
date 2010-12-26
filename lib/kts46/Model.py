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

import random, json, math, logging, yaml
from datetime import timedelta
from Car import Car
from Road import Road
from TrafficLight import SimpleSemaphore

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
        self._loggerName = 'roadModel'
        self._logger = logging.getLogger(self._loggerName)
        self._lastCarId = -1

    def run_step(self, milliseconds):
        stopDistance = self.params.safeDistance
        newCarGenRate = timedelta(seconds=self.params.carGenerationInterval)

        timeStep = timedelta(milliseconds=milliseconds)
        newTime = self.time + timeStep # Time after step is performed.

        for light in self._lights:
            if newTime > light.getNextSwitchTime():
                light.switch(newTime)

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
                nearestCar = self.get_nearest_car(car.get_position())
                if nearestCar is not None:
                    nearestCarBack = nearestCar.get_position() - nearestCar.get_length()
                    possiblePosition = nearestCarBack - stopDistance
                    if possiblePosition - car.get_position() < distanceToMove:
                        distanceToMove = possiblePosition - car.get_position()
                        if distanceToMove < 0:
                            distanceToMove = 0.0

                car.move(distanceToMove)
                if self._road.get_length() < car.get_position():
                    # self._cars.remove(car)
                    car.state = Car.DELETED
            else:
                self._cars.remove(car)

        # If there is a car in the queue, then send it.
        if len(self._enterQueue) > 0 and self.canAddCar():
            self._addCar(self._enterQueue[0])
            del self._enterQueue[0]

        # Generate new car.
        # If car was added from the queue then there is no possibility to add
        # car to the road, but it can be added to the queue so we still need to
        # run this step.
        if self._lastCarGenerationTime + newCarGenRate <= newTime:
            speedMultiplier = self.params.maxSpeed - self.params.minSpeed
            speedAdder = self.params.minSpeed
            speed = math.floor(random.random() * speedMultiplier) + speedAdder
            self._lastCarId += 1
            newCar = Car(id=self._lastCarId, speed=speed)
            self._lastCarGenerationTime = newTime
            self._logger.debug('Created car: {speed: %f}.', speed)
            if self.canAddCar():
                self._addCar(newCar)
            else:
                self._enterQueue.append(newCar)
                self._logger.info("Couldn't add car to the road, put in the queue.")

        # Update time.
        self.time = newTime


    def get_nearest_traffic_light(self, position):
        return self.get_nearest_object_in_array(self._lights, position)

    def get_nearest_car(self, position):
        return self.get_nearest_object_in_array(self._cars, position)

    def get_nearest_object_in_array(self, array, position):
        current = None
        current_pos = -1.0 # just to make sure :)
        for i in array:
            # Rule out deleted cars.
            if not hasattr(i, "state") or i.state != Car.DELETED:
                pos = i.get_position()
                if hasattr(i, "get_length"):
                    pos -= i.get_length()
                if pos > position and ((current is None) or current_pos > pos):
                    current = i
                    current_pos = pos
        return current

    def canAddCar(self):
        lastCar = self.get_nearest_car(-100.0) # Detect cars which are comming on the road.
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
        #for car in self._cars:
        #    if car.get_id() in self._lastSendCars:
        #        cars[car.get_id()] = car.get_state_data()
        #        del self._lastSendCars[car.get_id()]
        #    else:
        #        state = car.get_state_data()
        #        state['action'] = 'add'
        #        cars[car.get_id()] = state
        ## Delete old cars.
        #for carId, carValue in self._lastSendCars.iteritems():
        #    if ("action" not in carValue) or carValue["action"] != "del":
        #        cars[carId] = {'action': 'del'} # No need to send invalid state.
        #self._lastSendCars = cars
        # Result.
        return {'cars': cars, 'lights': lights}

    def get_description_data(self):
        data = {}
        data['lights'] = {}
        for light in self._lights:
            data['lights'][light.get_id()] = light.get_description_data()
        if self._road is not None:
            data['road'] = {'length': self._road.get_length(), 'width': self._road.get_width()}
        return json.dumps(data)

    def loadYAML(self, yamlData):
        objData = yaml.safe_load(yamlData)
        # fields
        if "carGenerationInterval" in objData:
           self.params.carGenerationInterval = objData["carGenerationInterval"]
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
        d["carGenerationInterval"] = self.params.carGenerationInterval
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
