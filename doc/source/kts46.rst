**************************
kts46 Python API Reference
**************************

.. automodule:: kts46


simulationServer
================
.. automodule:: kts46.simulationServer

.. autofunction:: kts46.simulationServer.timedeltaToSeconds


SimulationServer
----------------
.. autoclass:: kts46.simulationServer.SimulationServer
    :members:


statisticsServer
================
.. automodule:: kts46.statisticsServer

StatisticsServer
----------------
.. autoclass:: kts46.statisticsServer.StatisticsServer
    :members:


utils module
============
.. automodule:: kts46.utils
    :members:


mongodb module
==============
.. automodule:: kts46.mongodb
.. autoclass:: kts46.mongodb.Storage
    :members: createProject, __getitem__, __contains__, __delitem__, getProjectNames
.. autoclass:: SimulationProject
    :members: addJob, __getitem__, __contains__, __delitem__, getJobsNames, getJobs
.. autoclass:: SimulationJob
    :members: getStateDocumentId, __getitem__, __contains__, save
.. autoclass:: StateStorage
    :members:


kts46.server
============

.. automodule:: kts46.server


database
--------
.. automodule:: kts46.server.database

DatabaseServer
~~~~~~~~~~~~~~
.. autoclass:: kts46.server.database.DatabaseServer
    :members:


json_api
--------
.. automodule:: kts46.server.json_api

JSONApiServer
~~~~~~~~~~~~~
.. autoclass:: kts46.server.json_api.JSONApiServer
    :members:

JSONApiRequestHandler
~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: kts46.server.json_api.JSONApiRequestHandler
    :members:


rpc
---
.. automodule:: kts46.server.rpc

RPCServer
~~~~~~~~~
.. autoclass:: kts46.server.rpc.RPCServer
    :members:


status
------
.. automodule:: kts46.server.status

StatusServer
~~~~~~~~~~~~
.. autoclass:: kts46.server.status.StatusServer
    :members:


supervisor
----------
.. automodule:: kts46.server.supervisor

Supervisor
~~~~~~~~~~
.. autoclass:: kts46.server.supervisor.Supervisor
    :members:

worker
------
.. automodule:: kts46.server.worker

Worker
~~~~~~
.. autoclass:: kts46.server.worker.Worker
    :members:

WorkerException
~~~~~~~~~~~~~~~
.. autoclass:: kts46.server.worker.WorkerException
    :members:


kts46.model
===========
.. automodule:: kts46.model

Car
---
.. autoclass:: kts46.model.Car.Car
    :members:

Model
-----
.. autoclass:: kts46.model.Model.Model
    :members:

Road
----
.. autoclass:: kts46.model.Road.Road
    :members:

TrafficLight
------------
.. autoclass:: kts46.model.TrafficLight.SimpleSemaphore
    :members:
