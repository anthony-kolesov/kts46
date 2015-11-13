# Statistics #

There is one statistics document per simulation job). They are stored in `statistics` collection of database and has the same id as owning job. It fields are:
  * `finished` (bool), deprecated.
  * `average` (float)
  * `stdeviation` (float)
  * `averageSpeed` (float)
  * `idleTimes` (dictionary)
  * `throughput` (array).

# Progress #

Like statistics progresses are stored in collection `progresses` with id same as job id. Fields:
  * `totalStep` (int) - amount of simulation steps to do
  * `done` (int) - amount of steps already done
  * `batches` (int) - amount of job parts
  * `currentFullState` (YAML) - current full state of model
  * `basicStatistics` (bool)
  * `idleTimes` (bool)
  * `throughput` (bool)
  * `fullStatistics` (bool).