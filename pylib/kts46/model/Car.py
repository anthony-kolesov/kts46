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

import logging
from uuid import uuid4

class Car(object):
    "Represent a car in the model."

    INACTIVE = 'inactive'
    ADDED = 'add'
    ACTIVE = 'active'
    DEFAULT = 'active'
    DELETED = 'del'


    def __init__(self, model, road, id=None, speed=15, length=4.5, width=1.5, position=0,
                line=0):
        """Initializes a new car object.

        Creates new car using given parameters. Speed is measured in m/s, length,
        width and position in metrs.
        """
        if id is None:
            self.id = str(uuid4())
        else:
            self.id = str(id)
        self.model = model
        self.road = road
        self.desiredSpeed = speed
        self.length = length
        self.width = width
        self.position = position
        self.line = line
        self.state = Car.INACTIVE


    def move(self, distance):
        """Moves car on specified distance forward.

        :param distance: Distance in meters on which to move. Can't be negative.
        :type distance: float
        """
        if distance < 0:
            msg = "Distance of car moving can't be negative. " + \
                "Backwards moving isn't currently allowed."
            logging.getLogger('roadModel').error(msg)
            raise Exception(msg)
        self.position += distance


    def getDescriptionData(self):
        """Get dictionary with data describing this car.

        :rtype: dict"""
        return {'id': self.id,
                'length': self.length,
                'width': self.width,
                'desiredSpeed': self.desiredSpeed
        }


    def getStateData(self):
        """Get data describing current state of car.

        :rtype: dict"""
        d = {'pos': round(self.position, 2),
             'line': self.line
        }
        if self.state != Car.DEFAULT:
            d['state'] = self.state
        return d

    def load(self, description, state={}):
        self.id = description['id']
        self.length = description['length']
        self.width = description['width']
        self.desiredSpeed = description['desiredSpeed']
        if 'pos' in state: self.position = state['pos']
        if 'line' in state: self.line = state['line']

    def getDistanceToLeadingCar(self, line=None):
        """Get distance (in meters) to the leading car. If there is not leading
        car then None value will be returned."""
        if line is None:
            line = self.line
        leadingCar = self.model.getNearestCar(self.position, line)
        if leadingCar is not None:
            return leadingCar.position - self.position
        else:
            return None
    
    def getDistanceToFollowingCar(self, line=None):
        """Get distance (in meters) to the following car. If there is not
        following car then None value will be returned. Note that car which
        front is between current car front and rear is considered following. So
        this function will return distance between cars fronts. To check for
        safeDistanceRear one must negate self.length from the result.
        """
        if line is None:
            line = self.line
        # Get distances between cars fronts, so car that is a the same level
        # will be like following.
        followingCar = self.model.getFollowingCar(self.position, line)
        if followingCar is not None:
            return self.position - followingCar.position
        else:
            return None

    def chooseBestLine(self):
        """Chooses best line for current car on the basis of distance to leading
        car. Algorithm choses only between neighbor lines."""
        
        # Can't change line.
        if self.road.lines == 1:
            return self.line
        
        currentDistance = self.getDistanceToLeadingCar()
        rightDistance = self.canChangeLine(self.line - 1) if self.line > 0 else None
        leftDistance = self.canChangeLine(self.line + 1) if self.line + 1 < self.road.lines else None
        
        maxLine = self.line
        maxDistance = currentDistance
        # First try left.
        if leftDistance is not None and leftDistance > maxDistance:
            maxLine = self.line + 1
            maxDistance = leftDistance
        if rightDistance is not None and rightDistance > maxDistance:
            maxLine = self.line - 1
            maxDistance = rightDistance
        
        return maxLine
        
    def canChangeLine(self, targetLine):
        """Determines whether car can move to specified line with regard to
        safe distances.
        
        :param int targetLine: Line for which to perform check.
        :returns:
            distance to leading car if possible or None value if isn't possible.
        :rtype: float
        """
        leading = self.getDistanceToLeadingCar(targetLine)
        if leading is None or leading < self.model.params.safeDistance:
            return None
        following = self.getDistanceToFollowingCar(targetLine)
        if following is None or following - self.length < self.model.params.safeDistanceRear:
            return None
        return leading
