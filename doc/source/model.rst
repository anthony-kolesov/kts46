*****************
Model description
*****************

Algorithms that are used in model are described in this document.


Overtaking
==========

Algorithm
---------

#. Compare current apeed with desired. If current speed is greater greater then
   or equal to desired then car doesn't need to change line.
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