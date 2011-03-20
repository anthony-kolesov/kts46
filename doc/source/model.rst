*****************
Model description
*****************

Algorithms that are used in model are described in this document.

.. toctree::
    :maxdepth: 2
    :numbered:

    ModelChangelog.rst


Moving equation
===============

#. Get current speed of leading car.
#. Get predicted distance to leading car.
#. Get own new possible distance on the base of predicted distance and safe distance.

So equation of vehicle own speed on time interval is:

..math::
    :label: getOwnDistance

    S_{own}=S_{cur} + V_{leading} * t_{step} - S_{safe}
    0 \le S_{own} \le S_{desired}



Moving
======

Algorithm
---------
To take into account traffic lights one must limit desiredDistance by
distance allowed by traffic light.

#. Get own distance using :eq:`getOwnDistance` for current line.
#. If own distance is lesser then desired distance try neighbor lines:
  * Check that distance to following car is greater than or equal to
    ``safeDistanceRear``.
  * Get possible own distances on available lines using :eq:`getOwnDistance`.
  * Choose line with maximum distance.
  * If distances are equal, than lines are choosen according to priority:
    current, left, right. Thus overtaking will be done on left line.


First version of algorithm
--------------------------

#. Compare current speed with desired. If current speed is greater then or equal
   to desired then car doesn't need to change line.
#. Get distances to leading and following cars on adjacent lines.
#. Compare distances to leading cars and choose line accoring to rules:

  * If this is other line than distance to following car must be greater than
    or equal to backward safe distance.
  * Distance to leading car must be biggest.
  * If distances are equal, than lines are choosen according to priority:
    current, left, right. Thus overtaking will be done on left line.

To do
-----

* Use speed of leading car in line. If it is too slow than it will only make
  things worse. But that is important only if it is close enougth. So actually
  that is f(actual speed, distance to it).
* Make more strategic decisions: move not only to +-1 line but more (in several
  steps).


Model parameters
================

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
