.. _kts46-cn-schedulerapi:

Scheduler JSON-RPC API
======================

Scheduler listenes by default on port 46400 and accepts JSON-RPC calls with
address ``/jsonrpc``.

This API replace first version of scheduler API described
`here <http://code.google.com/p/kts46/wiki/SchedulerAPI>`_.

.. note::
    `JSON-RPC v1.0 <http://json-rpc.org/wiki/specification>`_ is used.

.. note::
    Also please note that if documentation says that "function throws exception
    DuplicateTask", than actually that means that content of reponse
    ``error.type`` field will be "DuplicateTask". If explicitly said in
    documentation error object may contain other fields with more specific
    description of error, mainly ``msg`` field.

All methods throws ``InvalidArgumentType`` error if arguments has an invalid
type. ``error.argumentName`` will contain name of failed argument. Example
values:

* ``projectName`` - for argument itself
* ``taskType[1]`` - if argument is array and contains object of invalid type
* ``taskType.field`` - same as array but for dictionary.

To run nodejs requires following modules: ``mongodb-native``, ``jsonrpc`` and
``config``.


Methods
-------

.. js:function:: hello()

    Just to be able to check whether server is alive.

    :returns: String with greeting.

    .. note::

        Proposed feature: return not a string, but an object with some
        information about node, like version and supported features.


.. js:function:: addTask(projectName, jobName)

    Adds to queue of waiting tasks new task for the specified job. If simulation
    hasn't been done then simulation task will be added. When simulation will be
    finished following statistics tasks will be added. Statistics types can be
    performed independently of each other and will be scheduled as different
    tasks.

    :param string projectName: Name of project to which task belongs.
    :param string jobName: Name of job that is executed in this task.
    :returns: "success" string. May become a dictionary in future.
    :throws DuplicateTask:
        Task for this job is already running. ``error.taskType`` field of
        object will contain name of failed task type.
    :throws AlreadyDone:
        Explicitly specified task is alread done. ``error.taskType`` will have
        failes taskType type.
    :throws JobNotFound: Specified job or project doesn't exists.


.. js:function:: abortTask(projectName, jobName)

    Aborts currently running tasks for specified job. Please note that it
    doesn't guaranteed that tasks currently running on workers will be aborted.

    :param string projectName: Name of project to which task belongs.
    :param string jobName: Name of job for which to abort task.
    :returns:
        (int) Number of directly aborted tasks. Dependent tasks doesn't count.
        So if zero is returned there were no active tasks for this job.


.. js:function:: getTask(workedId, taskTypes)

    This method is called by workers to get tasks to run. Worker must also call
    :js:func:`acceptTask` method before it will be finally assigned to it.

    :param string workerId:
        Unique identifier of worker. Worker can has only one tasks assigned to
        it at a time so no any workers must have same ids.
    :param arrayOfString taskTypes:
        Defines which tasks types worker accepts. Please note that unlike
        :js:func:`addTask` that is always array. Empty array isn't an error:
        schudler will just return no task.
    :throws UnknownTaskType:
        Specified task type is unknown to scheduler. ``error.taskType`` will
        contain name of this unknown type.
    :throws WorkerHasTask:
        This worker already has assigned task: either active or waiting
        acception from worker.
    :returns:
        :ref:`kts46-cn-taskType`. If there are tasks than ``empty`` will be
        ``false`` otherwise ``false``.


.. js:function:: acceptTask(workerId, sig)

    That method notifies scheduler that worker has accepted task and started it
    execution.

    :param string workerId: Worker unique identifier.
    :param string sig: Unique signature of task state.
    :returns:
        Dictionary with one field ``sig``  which contains new task state
        signature.
    :throws InvalidWorkerId:
        There is no task waiting for acception from this worker.
    :throws InvalidSignature:
        Signature for this task doesn't match. May be somebody has done with
        with task. Worker should call :js:func:`getTask` again for a new job.


.. js:function:: rejectTask(workerId, sig)

    With this method worker notifies scheduler that it rejects provided task.
    This method is different from restartign task by supervisor: supervisor will
    put task in the end of waiting queue, while this method will return it to
    the start of queue.

    :param string workerId: Worker unique identifier.
    :param string sig: Unique signature of task state.
    :returns: "success" string. May become a dictionary in future.
    :throws InvalidWorkerId:
        There is no task waiting for acception from this worker.
    :throws InvalidSignature:
        Signature for this task doesn't match. May be somebody has done with
        with task. Worker should call :js:func:`getTask` again for a new job.


.. js:function:: taskFinished(workerId, sig[, statistics])

    Notifies scheduler that worker has finished task. Scheduler may start
    following tasks if there are any.

    :param string workerId: Worker unique identifier.
    :param string sig: Unique signature of task state.
    :param statistics:
        Statistics of execution. Type: :ref:`kts46-cn-workerStatisticsType`.
    :returns: "success" string. May become a dictionary in future.
    :throws InvalidWorkerId:
        There is no running task for this worker.
    :throws InvalidSignature:
        Signature for this task doesn't match. May be somebody has done with
        with task. Worker can do nothing with this and should get a new job.


.. js:function:: taskInProgress(workerId, sig)

    Notifies scheduler that worker is alive and working on its task.

    :param string workerId: Worker unique identifier.
    :param string sig: Unique signature of task state.
    :returns:
        Dictionary with one field ``sig`` which contains new task state
        signature.
    :throws InvalidWorkerId:
        There is no running task for this worker.
    :throws InvalidSignature:
        Signature for this task doesn't match. May be somebody has done with
        with task. Worker can do nothing with this and should get a new job.


.. js:function:: getCurrentTasks()

    Returns list of currently active tasks.

    :returns:
        An array of objects with two fields: ``id`` is a worker id, and ``sig``
        is a signature of task state that is its last update time represented as
        a string. Both accepted and waiting for acception tasks are in this array.


.. js:function:: restartTasks(tasks)

    Restarts tasks. This method is intented to use by supervisor to avoid tasks
    staled because of dead workers. This method is used to restart tasks
    which are in active state and those that are waiting for acception.
    Scheduler must restart them properly according to algorithm for
    corresponsing task type.

    :param array tasks:
        Tasks to reset. Array contains objects with two fields: ``id`` is a
        worker id and ``sig`` is a task state signature. If signature or id
        doesn't match with known values scheduler will skip them quitly.
    :returns:
        A dictionary with one field: ``restarted`` with a number of restarted
        tasks.


Types
-----

.. _kts46-cn-taskType:

task
^^^^

.. js:attribute:: task.empty

    Whether object contains task. If it ``true`` than this dictionary will
    contain no other fields.

.. js:attribute:: task.project

    Name of project to which task belongs.

.. js:attribute:: task.job

    Name of job to which task belongs.

.. js:attribute:: task.type

    One of :ref:`kts46-cn-taskTypes` values which define what kind of work to do.

.. js:attribute:: task.sig

    String that is signature of task state. With help this fields scheduler may
    be sure that it is in sync with worker. For example when supervisor restarts
    task scheduler and signatures doesn't match that meen that state of task has
    been changed and worker is presumably alive.

.. js:attribute:: task.databases

    Array of objects that are paths to databases. Each object contains two
    fields: ``host`` - a string with database host, and ``port`` - an integer
    width database port on the host. Worker must try to use them starting from
    first, if it doesn't work try to use second and so on.

.. js:attribute:: task.startState

    Integer number to specify starting state for simulation. This attribure
    makes sense only for simulation tasks and doesn't provided for other tasks.

.. js:attribute:: task.notificationInterval

    Integer value that specifies number of millisecond that is the timer
    interval of how often worker must notify scheduler that it is alive.


.. _kts46-cn-workerStatisticsType:

workerStatistics
^^^^^^^^^^^^^^^^

.. js:attribute:: workerStatistics.project

    ``[string]`` Name of task project. This property is set by scheduler.

.. js:attribute:: workerStatistics.job

    ``[string]`` Name of task job. This property is set by scheduler.

.. js:attribute:: workerStatistics.taskType

    ``[string]`` Name of task type. This proeprty is set by scheduler.

.. js:attribute:: workerStatistics.executionTime

    ``[number]`` Number of seconds between start of task execution and its end. This value is
    calculated by scheduler, not worker.

.. js:attribute:: workerStatistics.hostName

    ``[string]`` Name of host on which worker is started.

.. js:attribute:: workerStatistics.vmPeak

    ``[number]`` Peak value of virtual memory usage in MiB.

.. js:attribute:: workerStatistics.vmRSS

    ``[number]`` Used resident memory at end of task in MiB.

.. js:attribute:: workerStatistics.version

    Version of worker.


Constants
---------

.. _kts46-cn-taskTypes:

Task types
^^^^^^^^^^

* ``taskType.simulation``: ``simulation``
* ``taskType.basicStatistics``: ``basicStatistics``
* ``taskType.idleTimes``: ``idleTimes``
* ``taskType.throughput``: ``throughput``
* ``taskType.fullStatistics``: ``fullStatistics``.
