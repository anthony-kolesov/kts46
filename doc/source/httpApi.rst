HTTP API
========

kts46 provides HTTP API to manage projects and jobs. This API is used by WebUI.
Management API provides JSON-RPC calls to control jobs: add, remove and simulate.
Data API provides GET requests to retrieve data about jobs state and simulation
results. HTTP API server listenes by default on port 46401. Data API has an
address ``/api/data`` and Management API ``/api/jsonrpc``.


.. toctree::
    :maxdepth: 2
    :numbered:

    ManagementAPI.rst
    DataAPI.rst
