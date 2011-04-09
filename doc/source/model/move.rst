Moving
======



Terms
-----

Maximum desired speed
    Maximum speed that is desired by this vehicle at current road.

Desired speed
    That is *current speed* + *possible acceleration*. This couldn't be greater
    than maximum desired speed. And it can limited by traffic light.

Possible distance
    That is desired distance also limited by leading car and its predicted speed.

Safe distance:
    That is braking distance plus reaction time distance for current speed plus
    minimal distance.

    .. math::
        :label: safe distance

        S_{safe} = V_{cur} * ( V_{cur} / 2 * a_{comf} + t_{reaction} ) + S_{min}


Algorithm
---------

1. Get desired distance for current line.
2. Get possible distance limited by leading car for current line.
3. If possible distance is lesser than desired try neighbor lines:

  * Check that distance to following car is greater than or equal to
    ``safeDistanceRear``.
  * Get possible distances on available lines.
  * Choose line with maximum distance.
  * If distances are equal, than lines are choosen according to priority:
    current, left, right. Thus overtaking will be done on left line if possible.


Acceleration and braking limits
-------------------------------

Cars can't instanly change speed. They have technical limits for this. To
simplify it is stated that cars reach 100 km/h in 13.5 seconds, thus maximum
acceleration is 2 m/s^2. Braking consists if two parts: reaction time that is
constant and is said to be 0.8 seconds in model (`see here for details <http://goo.gl/qpwD6>`_).
Actual braking of car is limited by 6.5 m / s^2. That gives the braking distance
of about 21.4 m from 60 km/h. There is also minimal distance that we want to keep
to leading car when cars don't move.
