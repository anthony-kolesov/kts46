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
import kts46.utils

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
        self.currentSpeed = speed
        self.length = length
        self.width = width
        self.position = position
        self.line = line
        self.state = Car.INACTIVE


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
             'line': self.line,
             'curspd': self.currentSpeed
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
        if 'curspd' in state: self.currentSpeed = state['curspd']
        if 'state' in state: self.state = state['state']

    #def getDistanceToLeadingCar(self, line=None):
    #    """Get distance (in meters) to the leading car. If there is not leading
    #    car then None value will be returned."""
    #    if line is None:
    #        line = self.line
    #    leadingCar = self.model.getNearestCar(self.position, line)
    #    if leadingCar is not None:
    #        return leadingCar.position - self.position
    #    else:
    #        return None

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

    def canChangeLine(self, targetLine, time):
        """Determines whether car can move to specified line with regard to
        safe distances.

        :param int targetLine: Line for which to perform check.
        :returns:
            distance to leading car if possible or None value if isn't possible.
        :rtype: float
        """
        following = self.getDistanceToFollowingCar(targetLine)
        if following is not None and following - self.length < self.model.params['safeDistanceRear']:
            return None

        #leading = self.getDistanceToLeadingCar(targetLine)
        #if leading is None or leading < self.model.params.safeDistance:
        #    return None
        leadingDistance = self.getOwnDistance(time, targetLine)
        if leadingDistance < 0:
            return None

        return leadingDistance

    def getDesiredDistance(self, time):
        """Returns desired moving distance for car for given time interval.

        :param timedelta time: Time for which to calculate moving distance."
        :rtype: float"""
        distance = self.desiredSpeed * kts46.utils.timedeltaToSeconds(time)
        return distance

    def getPredictedDistance(self, time):
        """Returns predicted moving distance for car for given time interval on
        the base of current car speed.

        :param timedelta time: Time for which to calculate moving distance."
        :rtype: float"""
        distance = self.currentSpeed * kts46.utils.timedeltaToSeconds(time)
        return distance

    def getOwnDistance(self, time, line=None):
        """Calculates possible distance that can be passed on the specified line
        for the specified interval of time. If returned value is negative, than
        you couldn't move to that line because of safe distance limit. Values is
        limited by desired distance."""
        if line is None: line = self.line

        # Need to add little value so car will not think of itself as a leader.
        startPosition = self.position if line != self.line else self.position + 0.1
        leader = self.model.getNearestCar(startPosition, line)
        if leader is None:
            return self.getDesiredDistance(time)

        distanceToLeader = leader.position - leader.length - self.position
        leaderMove = leader.getPredictedDistance(time)
        safeDistance = self.model.params['safeDistance']
        possibleDistance = distanceToLeader + leaderMove - safeDistance

        return min(possibleDistance, self.getDesiredDistance(time))

    def prepareMove(self, time):
        # Change state
        if self.state == Car.ADDED:
            self.state = Car.ACTIVE

        # Get own speed using :eq:`getOwnSpeed`.
        currentLineDistance = max(self.getOwnDistance(time, self.line), 0)
        # If own speed is lesser then desired speed try neighbor lines.
        desiredDistance = self.getDistanceAllowedByTL(time)
        # currentLineDistance still could be greater because desired is limited
        # by TL. So if only TL limits our movement we will stay at a line.
        if self.road.lines == 1 or currentLineDistance >= desiredDistance:
            finalDistance = min(desiredDistance, currentLineDistance)
            finalLine = self.line
        else:
           #  * Check that distance to following car is greater than or equal to safeDistanceRear.
           #  * Get possible own speeds on available lines using :eq:`getOwnSpeed`.
           if self.line > 0:
               leftDistance = self.canChangeLine(self.line - 1, time)
           else:
               leftDistance = None
           if self.line + 1 < self.road.lines:
               rightDistance = self.canChangeLine(self.line + 1, time)
           else:
               rightDistance = None

           # Choose line with maximum distance.
           # If speeds are equal, than lines are choosen according to priority:
           #   current, left, right. Thus overtaking will be done on left line.
           finalLine = self.line
           finalDistance = currentLineDistance
           # First try left.
           if leftDistance is not None and leftDistance > finalDistance:
               finalLine = self.line - 1
               finalDistance = leftDistance
           if rightDistance is not None and rightDistance > finalDistance:
               finalLine = self.line + 1
               finalDistance = rightDistance

        newPosition = self.position + finalDistance
        self.newState = {
            'line': finalLine,
            'position': newPosition,
            'speed': finalDistance / kts46.utils.timedeltaToSeconds(time)
        }
        if self.road.length < newPosition:
            self.newState['state'] = Car.DELETED


    def finishMove(self):
        self.line = self.newState['line']
        self.position = self.newState['position']
        self.currentSpeed = self.newState['speed']
        if 'state' in self.newState: self.state = self.newState['state']

    def getDistanceAllowedByTL(self, time):
        nearestTL = self.model.getNearestTrafficLight(self.position)
        desiredDistance = self.getDesiredDistance(time)
        if nearestTL is not None and not nearestTL.isGreen:
            stopDistance = self.model.params['trafficLightStopDistance']
            distanceToTL = max(nearestTL.position - self.position - stopDistance, 0)
            desiredDistance = min(distanceToTL, desiredDistance)
        return desiredDistance
