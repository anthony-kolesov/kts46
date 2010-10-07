import datetime, random
from xpcom import components, verbose
from Car import Car
#from TrafficLight import SimpleSemaphore
#from Road import Road

class RoadNetworkModel:
    _com_interfaces_ = components.interfaces.nsIRoadNetworkModel
    _reg_clsid_ = "{efabba84-e20e-46b6-98bb-ef67fc0ab496}"
    _reg_contractid_ = "@kolesov.blogspot.com/RoadNetworkModel;1"

    def __init__(self):
        self._time = datetime.timedelta()
        self._cars = []
        self._lights = []
        #self._road = Road(length=300)
        self._lastCarGenerationTime = datetime.timedelta()
        self._value = 0

    def __del__(self):
        if verbose:
            print("RoadNetworkModel: __del__ method called - object is destructing")

    def run_step(self, milliseconds):
        stopDistance = 2.0
        newCarGetRate = datetime.timedelta(second=3)

        timeStep = datetime.timedelta(milliseconds=milliseconds)
        newTime = self._time + timeStep # Time after step is performed.

        for light in self._lights:
            if newTime - light.get_last_switch_time() > light.get_interval():
                light.switch(newTime)

        for car in sel._cars:
            distanceToMove = car.get_speed() * timeStep.seconds
            distanceToMove += car.get_speed() * timeStep.microseconds * 1e-6
            distanceToMove += car.get_speed() * timeStep.days * 86400 # 3600 * 24

            # Check for red traffic light.
            nearestTL = self.get_nearest_traffic_light(car.get_position())
            if nearestTL is not None and not nearestTL.is_green() and \
                nearestTL.get_position() - car.get_position() - stopDistance < distanceToMove:
                diatnceToMove = nearestTL.get_position() - car.get_position() - stopDistance
                if distanceToMove < 0:
                    distanceToMove = 0.0

            # Check for leading car.
            nearestCar = self.get_nearest_car(car.get_position())
            if nearestCar is not None and \
              nearestCar.get_position() - nearestCar.get_length() - \
              car.get_position() - stopDistance() < distanceToMove:
                distanceToMove = nearestCar.get_position() - nearestCar.get_length() - \
                    car.get_position() - stopDistance
                if distanceToMove < 0:
                    distanceToMove = 0


            car.move(distanceToMove)
            if self._road.get_length() < car.get_position():
                self._cars.remove(car)

        # Generate new car
        if self._lastCarGenerationTime + newCarGenRate <= newTime:
            speed = math.floor(random.random() * 10) + 10
            newCar = Car(speed=speed)
            self._cars.append(car)
            self._lastCarGenerationTime = newTime

        self._time = newTime


    def get_nearest_traffic_lisht(self, position):
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
            if pos > position and ((current is not None) or current_pos > pos):
                current = i
                current_position = pos
        return current

    def get_current_state(self):
        return "AAAA! Values is: %i" % self._value

    #def run_step(self):
    #    self._value += 1
