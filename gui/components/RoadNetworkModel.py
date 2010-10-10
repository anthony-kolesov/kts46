import datetime, random, json, math
from xpcom import components, verbose
from Car import Car
from TrafficLight import SimpleSemaphore
from Road import Road

class RoadNetworkModel:
    _com_interfaces_ = components.interfaces.nsIRoadNetworkModel
    _reg_clsid_ = "{efabba84-e20e-46b6-98bb-ef67fc0ab496}"
    _reg_contractid_ = "@kolesov.blogspot.com/RoadNetworkModel;1"

    def __init__(self):
        self._time = datetime.timedelta()
        self._cars = []
        self._lastSendCars = []
        self._lights = []
        self._road = Road(length=300)
        self._lastCarGenerationTime = datetime.timedelta()
        self._log = components.classes['@mozilla.org/consoleservice;1'].getService(components.interfaces.nsIConsoleService)
        self._log.logStringMessage("Log is configured.")
        # config default model
        self._lights.append(SimpleSemaphore(id=1, position=30))

    def __del__(self):
        if verbose:
            print("RoadNetworkModel: __del__ method called - object is destructing")

    def run_step(self, milliseconds):
        stopDistance = 2.0
        newCarGenRate = datetime.timedelta(seconds=1)

        timeStep = datetime.timedelta(milliseconds=milliseconds)
        newTime = self._time + timeStep # Time after step is performed.

        for light in self._lights:
            if newTime - light.get_last_switch_time() > light.get_interval():
                light.switch(newTime)

        for car in self._cars:
            distanceToMove = car.get_speed() * timeStep.seconds
            distanceToMove += car.get_speed() * timeStep.microseconds * 1e-6
            distanceToMove += car.get_speed() * timeStep.days * 86400 # 3600 * 24

            # Check for red traffic light.
            nearestTL = self.get_nearest_traffic_light(car.get_position())
            if nearestTL is not None and not nearestTL.is_green():
                #self._log.logStringMessage("Calculating TL effect: "+
                #    "TL pos: %f, Car pos: %f, stop dist: %f, move dist: %f, diff: %f" % (
                #    nearestTL.get_position(), car.get_position(),
                #    stopDistance, distanceToMove, nearestTL.get_position() - car.get_position() - stopDistance) )
                if nearestTL.get_position() - car.get_position() - stopDistance < distanceToMove:
                    distanceToMove = nearestTL.get_position() - car.get_position() - stopDistance
                    if distanceToMove < 0:
                        distanceToMove = 0.0

            # Check for leading car.
            #nearestCar = self.get_nearest_car(car.get_position())
            #if nearestCar is not None and \
            #  nearestCar.get_position() - nearestCar.get_length() - \
            #  car.get_position() - stopDistance < distanceToMove:
            #    distanceToMove = nearestCar.get_position() - nearestCar.get_length() - \
            #        car.get_position() - stopDistance
            #    if distanceToMove < 0:
            #        distanceToMove = 0


            car.move(distanceToMove)
            if self._road.get_length() < car.get_position():
                self._cars.remove(car)

        # Generate new car
        if len(self._cars) < 2 and self._lastCarGenerationTime + newCarGenRate <= newTime:
            speed = math.floor(random.random() * 10) + 10
            newCar = Car(speed=speed)
            self._cars.append(newCar)
            self._lastCarGenerationTime = newTime

        self._time = newTime


    def get_nearest_traffic_light(self, position):
        return self.get_nearest_object_in_array(self._lights, position)

    def get_nearest_car(self, position):
        return self.get_nearest_object_in_array(self._cars, position)

    def get_nearest_object_in_array(self, array, position):
        current = None
        current_pos = 0.0
        for i in array:
            pos = i.get_position()
            if hasattr(i, "get_length"):
                pos -= i.get_length()
            if pos > position and ((current is None) or current_pos > pos):
                current = i
                current_pos = pos
        return current

    def get_state_data(self):
        # Traffic lights
        lights = {}
        for light in self._lights:
            lights[light.get_id()] = light.get_state_data()
        # Cars
        cars = {}
        for car in self._cars:
            if car.get_id() in self._lastSendCars:
                cars[car.get_id()] = car.get_state_data()
                del self._lastSendCars[car.get_id()]
            else:
                state = car.get_state_data()
                state['action'] = 'add'
                cars[car.get_id()] = state
        # Delete old cars.
        for (key, oldCar) in self._lastSendCars:
            cars[oldCar.get_id()] = {'action': 'del'} # No need to send invalid state.
        self._lastSendCars = cars
        # Result.
        return json.dumps({'cars': cars, 'lights': lights})

    def get_description_data(self):
        lights = {}
        for light in self._lights:
            lights[light.get_id()] = light.get_description_data()
        road = {'length': self._road.get_length(), 'width': self._road.get_width()}
        return json.dumps({'lights': lights, 'road': road})
