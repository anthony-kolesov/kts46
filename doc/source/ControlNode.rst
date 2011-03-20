****************
Control Node API
****************

This document describes an API of ControlNode based on NodeJS. This API consists
of several parts: scheduler API, project management API and data API. Also a web
user interface is hosted by the ControlNode. By default ControlNode listens on
port 46400. Management and Scheduler API shares same JSON-RPC endpoint which has
an address ``/api/jsonrpc`` and receives POST requests. Data API has an address
``/api/data`` which accepts GET request and returns various types of data.


.. toctree::
    :maxdepth: 2
    :numbered:

    SchedulerAPI.rst
    ManagementAPI.rst
    DataAPI.rst
