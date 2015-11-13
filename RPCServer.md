# Introduction #

rpc\_server.py provides an XML-RPC interface for simulation functionality. Here it's interface and internals are described.


# Details #

Firstly to do simulation it is required to create simulation project. This is done via function `createProject`. `projectExists` function allows to check whether project already exists and with `deleteProject` existing project can be deleted.

After project has been created a number of simulation job can be added. `addJob` function adds job to the project. Job is given an internal id in form of `j<id>` where `<id>` is an incrementing number. In database a name and YAML definition of project are saved. Job existence in database can be checked with function `jobExists` and it can be deleted with function `deleteJob`. If job is deleted all corresponding results of simulation will be deleted too. To count amount of jobs created a special document `jobsCount` is used.

Job simulation can be started via function `runJob`. Job must already exists in database and all data will be taken from it. Each simulation step will be stored with id `s<jobId>_<stateId>` where `stateId` is incremented each simulation step on one. Along with simulation data each state document also will contain following metadata: job id, simulation time, simulation step number.

To track progress of simulation when job is created there also will be created a document `j<jobId>Progress`. This document will be updated with each write of simulation steps to database, so external viewer can examine progress of current job simulations. Document will contain following data:
  * `job` (string) -- job id
  * `totalSteps` (int) -- amount of steps to simulate
  * `done` (int) -- amount of steps already simulated
  * `batches` (int) -- amount of batches to perform job. Batch length is stores in simulation parameters
  * `currentFullState` (YAML string) -- serialized full current state of document.


# Deletion #
When job is deleted all of its data is deleted also. This includes: all states with equal job id and job progress document.


# CouchDB implementation details #
Each project is stored in separate database. So if project has been deleted there is no need to do any specific removing operations. However it is required to create all views when project is created.