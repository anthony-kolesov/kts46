# Copyright 2010-2012 Anthony Kolesov
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

from Car import Car
from Crossroad import Crossroad
from Endpoint import Endpoint
from TrafficLight import SimpleSemaphore

class Road(object):
    "Defines a road in the model."

    def __init__(self, name, model, length=1000, width=10, lines=[1,1], points=[]):
        "Creates new road."
        self.name = name
        self.length = length
        self.width = width
        self.lines = lines
        directionCnt = 0
        self.cars = []
        self.trafficLights = set()
        
        # Setup endpoints and crossroads.
        self.points = []
        self.pointExits = []
        for pointDescription in points:
            point = model.getPoint(pointDescription[0])
            pointExitNumber = pointDescription[1]
            if isinstance(point, Endpoint):
                point.road = self
                point.direction = directionCnt
                directionCnt += 1
            if isinstance(point, Crossroad):
                point.roads[pointExitNumber] = self
                point.directions[pointExitNumber] = directionCnt
                
                # Check if crossroad has traffic lights.
                if point.trafficLight is not None:
                    greenDuration = point.trafficLight[ pointExitNumber % 2 ]
                    redDuration = point.trafficLight[ (pointExitNumber + 1 ) % 2 ]
                    tlState = 'g' if pointExitNumber % 2 == 0 else 'r'
                    tl = SimpleSemaphore(point.name + '_' + str(pointExitNumber),
                            greenDuration=greenDuration, redDuration=redDuration,
                            position=self.length - 20, direction=(directionCnt+1)%2,
                            state=tlState )
                    self.trafficLights.add(tl)
                directionCnt += 1

            self.points.append(point)
            self.pointExits.append(pointExitNumber)


    def getLinesForPoint(self, pointName):
        if self.points[0].name == pointName:
            return self.lines[0]
        else:
            return self.lines[1]


    def getDescriptionData(self):
        "Gets dictionary describing this road."
        return {#'length': self.length,
                #'width': self.width,
                #'lines': self.lines
               }
               
    def load(self, description):
        self.length = description['length']
        self.width = description['width']
        self.lines = description['lines']
        
    def isHorizontalRoad(self):
        return abs(self.points[0].coords['x'] - self.points[1].coords['x']) > abs(self.points[0].coords['y'] - self.points[1].coords['y'])


    def getNearestCar(self, position, direction, line=0):
        return self._getNearest(self.cars, position, direction, line)


    def getNearestStop(self, position, direction, line=0):
        tl = self._getNearest(self.trafficLights, position, direction, line)
        return tl


    def _getNearest(self, items, position, direction, line):
        position += 0.1
        current = None
        current_pos = -1.0 # just to make sure :)
        for i in items:

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
   
    
    def getFirstEndpoint(self, direction):
        return (self.points[direction], self.pointExits[direction])
 
    def getNextEndpoint(self, direction):
        if direction == 0:
            return (self.points[1], self.pointExits[1])
        else:
            return (self.points[0], self.pointExits[0])
