*************************
Control node JSON-RPC API
*************************

Here is a description of API of control node based on node.js. This API replace
first version of scheduler API described `here <http://code.google.com/p/kts46/wiki/SchedulerAPI>`_.

.. note::
    `JSON-RPC v1.0 <http://json-rpc.org/wiki/specification>`_ is used.

.. note ::
    Also please note that if documentation says that "function throws exception
    DuplicateTask", than actually that means that content of reponse
    ``error.type`` field will be "DuplicateTask". If explicitly said in
    documentation error object may contain other fields with more specific
    description of error, mainly ``msg`` field.

All method throws ``InvalidArgumentType`` error if arguments has an invalid
type. ``error.argumentName`` will contain name of failed argument. Example
values:

* ``projectName`` - for argument itself
* ``taskType[1]`` - if argument is array and contains object of invalid type
* ``taskType.field`` - same as array but for dictionary.


Methods
=======

.. js:function:: addTask(projectName, jobName[, taskType])

    Adds to queue of waiting tasks new task for the specified job. Task can
    derive several other tasks and some of them may be run simultaneously and
    scheduler will try to do so. For example to do anything with model results
    first simulation has to be done. Statistics types can be performed
    independently of each other and will be scheduled as different tasks.

    .. note::
        If multiple tasks are specified and if exception will be thrown it will
        correspond to first failed task type - other task types may have or may
        have not errors. Also if any task type throws error than no tasks will
        be added. That is, call of this method is atomic.

    :param string projectName: Name of project to which task belongs.
    :param string jobName: Name of job that is executed in this task.
    :param string-or-arrayOfStrings taskType:
        Specifies specific type of task that has to be done on job. If not
        specified than scheduler will do all available tasks for this job
        according to preferences. For available values see :ref:`kts46-cn-taskTypes`.
        If array of strings is provided than all of them will be scheduled. If
        any of specified types is unknown than nothing will be scheduled.
        Null values are ignored. Note that statistics tasks require simulation
        to be done. If dependencies are not done than scheduler will run them.
    :throws DuplicateTask:
        Explicitly specified task is already running. This can be thrown only to
        specified types. ``taskType`` field of ``error`` object will contain
        name of failed task type.
    :throws AlreadyDone:
        Explicitly specified task is alread done. ``error.taskType`` will have
        failes taskType type.
    :throws UnknownTaskType:
        Specified task type is unkown to scheduler. ``error.taskType`` will
        contain name of this unknown type.


.. js:function:: abortTask(projectName, jobName[, taskType])

    Aborts currently running tasks for specified job. If no ``taskType`` is
    specified than all tasks will be aborted. Please note that it doesn't
    guaranteed that tasks currently running on workers will be aborted.

    :param string projectName: Name of project to which task belongs.
    :param string jobName: Name of job for which to abort task.
    :param string-or-arrayOfStrings taskType:
        Specifies specific type of task to abort. Scheduler will abort all tasks
        that depend on specified task type.
    :returns:
        (int) Number of directly aborted tasks. Dependent tasks doesn't count.
        So if zero is returned there were no active tasks for this job.
    :throws UnknownTaskType:
        Specified task type is unkown to scheduler. ``error.taskType`` will
        contain name of this unknown type.


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
        Specified task type is unkown to scheduler. ``error.taskType`` will
        contain name of this unknown type.


.. js:function:: acceptTask(workerId)
.. js:function:: rejectTask(workerId)
.. js:function:: taskFinished(workerId)
.. js:function:: taskInProgress(workerId)
.. js:function:: getCurrentTasks()
.. js:function:: restartTasks()


Constants
=========

.. _kts46-cn-taskTypes:

Task types
----------

* ``taskType.simulation``: ``simulation``
* ``taskType.simulation``: ``basicStatistics``
* ``taskType.simulation``: ``idleTimes``
* ``taskType.simulation``: ``throghput``
* ``taskType.simulation``: ``fullStatistics``.
