Data API
========

Control node has an API to return data about states of scheduler, projects and
simulation and results. This is a an HTTP API which accepts GET requests. It
supports JSON, JSON-P and CSV (TSV) output. Type of output can be specified by
``type`` parameter. ``json`` is default, ``jsonp`` requires ``callback``
parameter, ``csv`` and ``tsv`` types are supported if output data can be
represented as table (see request documentation).

.. describe:: serverStatus

    Lists all tasks on server with their projects. This request has no
    parameters.Returns tabular data and supports CSV and TSV formats. Table has
    following columns:

        * project: string, project name
        * name: string, job name
        * totalSteps: integer, total amount of simulation steps to do
        * done: integer, amount of simulation steps done
        * basicStatistics: boolean, whether basic statistics has been calculated
        * idleTimes: boolean, whether idle times statistics has been calcualted
        * throughput: boolean, whether throughput statistics has been calculated
        * fullStatistics: boolean, whether all statistics has been calculated.


.. describe:: jobStatistics

    Returns job statistics. Requires two parameters: ``project`` and ``job``.
    Couldn't return tabular data.

.. describe:: modelDefinition

    Returns model definition. Requires two parameters: ``project`` and ``job``.

.. describe:: modelState

    Returns model state.  Required parameters: ``project``, ``job`` and ``time``.

.. describe:: listJobStatistics

    Returns job statistics of several jobs. Required parameter: array of jobs to
    return. This parameters has name ``q`` (query) and formatted as a coma
    separated list of pairs ``project:job``, e.g. ``?q=proj1:job1,proj2:job2``.
