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
