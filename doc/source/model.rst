*****************
Model description
*****************

Algorithms that are used in model are described in this document.


Moving
======

#. Get own desired speed.
#. Get current speed of leading car.
#. Get predicted distance to leading car.
#. Get own new current speed on the base of predicted distance and safe distance.

Since Pythagoras, we know that :math:`a^2 + b^2 = c^2`.
So equation of vehicle own speed on next time interval is:
:math:`V_own`



Overtaking
==========

Algorithm
---------

#. Compare current speed with desired. If current speed is greater then or equal
   to desired then car doesn't need to change line.
#. Get distances to leading and following cars on adjacent lines.
#. Compare distances to leading cars and choose line accoring to rules:

  * If this is other line than distance to following car must be greater than
    or equal to backward safe distance.
  * Distance to leading car must be biggest.
  * If distances are equal, than lines are choosen accoring to priority:
    current, left, right. Thus overtaking will be done on left line.

To do
-----

* Use speed of leading car in line. If it is too slow than it will only make
  things worse. But that is important only if it is close enougth. So actually
  that is f(actual speed, distance to it).
* Make more strategic decisions: move not only to +-1 line but more (in several
  steps).


Model parameters
----------------
inputRate
    Amount of cars comming to the road in an hour.

safeDistance
    Distance that is considered safe by drivers between car front and leading
    car back. Measurement: meters.

safeDistanceRear
    Distance that is considered safe by driver between her car rear and
    following car front.

maxSpeed
    Maximum desired speed of cars.

minSpeed:
    Minimum desired speed of cars.
