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

class Road(object):
    "Defines a road in the model."

    def __init__(self, name, length=1000, width=10, lines=[1,1], points=[]):
        "Creates new road."
        self.name = name
        self.length = length
        self.width = width
        self.lines = lines
        self.points = points
        directionCnt = 0
        self.cars = []
        for point in self.points:
            point.road = self
            point.direction = directionCnt
            directionCnt += 1


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
