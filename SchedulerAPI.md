# Introduction #

Here is described an API of scheduler, which can be used for communication between scheduler and worker agents. Page also covers some technical details of implementation.
This API is also used by supervisor to control stale tasks.



# Methods #

Scheduler provides following functions for clients:

  * `runJob(projectName, jobName)` - this function is called by client components and adds job to the execution queue. Now jobs doesn't have a priority, but it can be added in future.

  * `getJob(workerId)` - this function is called by workers to get job to do. If there is no available items in queue then `None` is returned. If there is item in queue then a dictionary is returned. Content of dictionary depends on type of job. This fields are present in all jobs:
    * project (string) - name of project to which job belongs
    * job (string) - name of job to do
    * timeout (int) - time in milliseconds between poll period. Worker must call 'reportStatus' function with periods no longer than this value to notify scheduler that worker is alive and job is being processed
    * type (string) - job type. May be `simulation` or `statistics`
    * lastUpdate (datetime) - time of last task update. It is used like hash or revision number to ensure that simulation will not be broken because of some parallel races or anything like this.

  * `reportStatus(workerId, state, lastUpdate)` - workers call this method to notify scheduler about their status. `workerId` is a string identifier of worker. Scheduler doesn't check the uniquecy of identifiers by any means, that is the job of an administrator. `lastUpdate` is a datetime of last status update of this worker. That is required to ensure that that nothing new happened after last time worker updated status. For example if supervisor restarted this task. `state` is a string that identifies state of worker. This can be:
    * `working` - worker is alive and processes job
    * `abort` - worker aborted it's current job
    * `finished` - all job is finished and data is stored on the server.

  * `getCurrentTasks` - this is a function intended to use by supervisor. It returns all current tasks with times of last status update from worker.

  * `restartTask(workerId, lastUpdate)` - this function is called by supervisor to restart task if it seems that worker doesn't respond in time. `workerId` is a string identifier of worker which task to restart. `lastUpdate` is a Python `datetime.datetime` object. It must be equal to that was send to supervisor in `getCurrentTasks`. If it isn't than it is assumed that status has been updated and restart is dropped. This function returns boolean value: `True` if task has been successfully restarted and `False` if `workedId` is unknown or `lastUpdate` doesn't match.

# Scheduler #

When started scheduler creates two shared queues for parallel access: `unstartedJobs` and `currentJobs`. When client calls `runJob` function job from database is split in batches. Size of batch is measured in simulation steps. When worker gets job it is removed from `unstartedJobs` and placed in a `currentJobs`. Also last worker communication time is stored. Supervisor will use this data to put aborted jobs again to `unstartedJobs`.