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

from Endpoint import Endpoint
from Crossroad import Crossroad
from Car import Car

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
        #self.nextRoad = None
        #self.previousRoad = None
        
        # Setup endpoints and crossroads.
        #roadData['points'][0] = self.getPoint(roadData['points'][0][0])
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
                directionCnt += 1
            self.points.append(point)
            self.pointExits.append(pointExitNumber)
                #oppositeRoad = point.roads[ (pointExitNumber + 2) % 4 ]
                #if oppositeRoad is not None:
                #    oppositeRoad


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
        position += 0.1
        current = None
        current_pos = -1.0 # just to make sure :)
        for i in self.cars:

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
    
    def getNextEndpoint(self, direction):
        if direction == 0:
            return (self.points[1], self.pointExits[1])
        else:
            return (self.points[0], self.pointExits[0])
