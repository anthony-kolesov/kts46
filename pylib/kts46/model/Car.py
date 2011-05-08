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
        width and position in metrs."""

        if id is None:
            self.id = str(uuid4())
        else:
            self.id = str(id)
        self.model = model
        self.road = road
        self.desiredSpeed = speed
        self.currentSpeed = 0.0
        self.length = length
        self.width = width
        self.position = position
        self.line = line
        self.state = Car.INACTIVE


    def getDescriptionData(self):
        """Get dictionary with data describing this car. Conains: id, length,
        width and desired speed.

        :rtype: dict"""
        return {'id': self.id,
                'length': self.length,
                'width': self.width,
                'desiredSpeed': self.desiredSpeed
        }


    def getStateData(self):
        """Get data describing current state of car: position (as ``pos``), line
        and current speed (as ``curspd``).

        :rtype: dict"""
        d = {'pos': round(self.position, 2),
             'line': self.line,
             'curspd': self.currentSpeed
        }
        if self.state != Car.DEFAULT:
            d['state'] = self.state
        return d


    def load(self, description, state={}):
        """Loads car from data description.

        :param description:
            dictionary with car definition (returned from getDescriptionData).
        :param state:
            dictionary with car current state (returned from getStateData).
        """
        self.id = description['id']
        self.length = description['length']
        self.width = description['width']
        self.desiredSpeed = description['desiredSpeed']
        if 'pos' in state: self.position = state['pos']
        if 'line' in state: self.line = state['line']
        if 'curspd' in state: self.currentSpeed = state['curspd']
        if 'state' in state: self.state = state['state']


    def getDistanceToFollowingCar(self, line=None):
        """Get distance (in meters) to the following car. If there is no
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


    def getPredictedDistance(self, time):
        """Returns predicted moving distance for car for given time interval on
        the base of current car speed.

        :param timedelta time: Time for which to calculate moving distance."
        :rtype: float"""
        distance = self.currentSpeed * kts46.utils.timedeltaToSeconds(time)
        return distance


    def prepareMove(self, time):
        """Calculates current car move but new parameters won't be saved to
        fields, other cars will make decisions on the basis of current car
        state, not future."""

        # Change state
        if self.state == Car.ADDED:
            self.state = Car.ACTIVE

        ts = kts46.utils.timedeltaToSeconds(time)

        brakingDistance = self.getBrakingDistance()
        desiredSpeed, desiredDistance = self.getDesiredDistance(ts)
        distanceToTL = self.getNearestTLDistance()

        # Get distance to leading car.
        distanceToLeadingCar = self.getDistanceToLeadingCar(ts, self.line)
        # Skip it if it is after red light.
        if distanceToTL is not None and distanceToTL < distanceToLeadingCar:
            distanceToLeadingCar = None

        # Does leading car restatrains us?
        if self.road.lines > 1 and distanceToLeadingCar is not None and distanceToLeadingCar <= brakingDistance:
            # Try other lines.
            if self.line > 0:
                leftDistance = self.getDistanceToLeadingCar(ts, self.line - 1)
                # Check for traffic light.
                if distanceToTL is not None and distanceToTL < leftDistance:
                    leftDistance = None
                # Check for rear safe distance but only if line wasn't already scrapped.
                if leftDistance is not None:
                    leftFollowing = self.getDistanceToFollowingCar(self.line - 1)
                    if (leftFollowing is not None and
                        leftFollowing - self.length < self.model.params['safeDistanceRear']):
                        leftDistance = None
            else:
                leftDistance = None

            if self.line + 1 < self.road.lines:
                rightDistance = self.getDistanceToLeadingCar(ts, self.line + 1)
                # Check for traffic light.
                if distanceToTL is not None and distanceToTL < rightDistance:
                    rightDistance = None
                # Check for rear safe distance but only if line wasn't already scrapped.
                if rightDistance is not None:
                    rightFollowing = self.getDistanceToFollowingCar(self.line + 1)
                    if (rightFollowing is not None and
                        rightFollowing - self.length < self.model.params['safeDistanceRear']):
                        rightDistance = None
            else:
                rightDistance = None

            # Choose line with maximum distance.
            # If speeds are equal, than lines are choosen according to priority:
            # current, left, right. Thus overtaking will be done on left line if possible.
            finalLine = self.line
            finalDistance = distanceToLeadingCar
            # First try left.
            if leftDistance is not None and leftDistance > finalDistance:
                finalLine = self.line - 1
                finalDistance = leftDistance
            if rightDistance is not None and rightDistance > finalDistance:
                finalLine = self.line + 1
                finalDistance = rightDistance
        else:
            finalLine = self.line
            if distanceToLeadingCar is not None:
                finalDistance = distanceToLeadingCar
            elif distanceToTL is not None:
                finalDistance = distanceToTL
            else:
                finalDistance = brakingDistance + 1.0

        if finalDistance <= brakingDistance:
            # Normal deacceleration.
            allowedDistance = finalDistance - self.model.params['minimalDistance']
            if allowedDistance > 0:
                deacceleration = self.currentSpeed * self.currentSpeed / (2.0 * allowedDistance)
                if deacceleration >= self.model.params["brakingLimit"]:
                    deacceleration = self.model.params["brakingLimit"]
                newSpeed = self.currentSpeed - deacceleration * ts
                if newSpeed < 0: newSpeed = .0
            else:
                deacceleration = .0
                newSpeed = .0
            newDistance = self.currentSpeed * ts - deacceleration * ts * ts / 2.0
            if newDistance < 0: newDistance = 0
        else:
            newSpeed = desiredSpeed
            newDistance = desiredDistance

        newPosition = self.position + newDistance
        self.newState = {
            'line': finalLine,
            'position': newPosition,
            'speed': newSpeed
        }
        if self.road.length < newPosition:
            self.newState['state'] = Car.DELETED


    def finishMove(self):
        "Stores caclculated new moving parameters."
        self.line = self.newState['line']
        self.position = self.newState['position']
        self.currentSpeed = self.newState['speed']
        if 'state' in self.newState: self.state = self.newState['state']


    def getBrakingDistance(self):
        a = self.model.params["comfortBrakingLimit"]
        #treaction = self.model.params["driverReactionTime"]
        treaction = 0.0
        smin = self.model.params["minimalDistance"]
        return self.currentSpeed * (self.currentSpeed/(2*a) + treaction) + smin


    def getDistanceToLeadingCar(self, interval, line):
        "Get distance to leading car including its predicted movement."
        # Get distance to leading car.
        leadingCar = self.model.getNearestCar(self.position, line)
        if leadingCar is None:
            return None
        else:
            return (leadingCar.position - leadingCar.length - self.position +
                    leadingCar.currentSpeed * interval)# - self.model.params['minimalDistance'])


    def getDesiredDistance(self, ts):
        """Get desired distance for car in following time cycle.

        :return: (desiredSpeed, desiredDistance)"""
        desiredSpeed = min(self.desiredSpeed,
            self.currentSpeed + self.model.params["accelerationLimit"] * ts)
        acceleration = max(desiredSpeed - self.currentSpeed, 0)
        desiredDistance = self.currentSpeed * ts + acceleration * ts * ts / 2.0
        return (desiredSpeed, desiredDistance)


    def getNearestTLDistance(self):
        "Returns distance to nearest traffic light or None if there is not any."
        nearestTL = self.model.getNearestTrafficLight(self.position)
        if nearestTL is not None and not nearestTL.isGreen:
            return nearestTL.position - self.position
        else:
            return None
