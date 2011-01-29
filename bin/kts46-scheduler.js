var mongodb = require('./mongodb');

// Scheduler constants
var taskType = { simulation: "simulation", basicStatistics: "basicStatistics",
  idleTimes: "idleTimes", throughput: "throughput",
  fullStatistics: "fullStatistics"
};


// Module locals
var waitingQueue = [];
var waitingActivation = {};
var runningTasks = {};
var projects = {};
var cfg = {};


// Util methods.
var checkType = function(rpc, arg, argname, type) {
  if (typeof(arg) !== type) {
    var err = {"type": "InvalidArgumentType", "argumentName": argname};
    rpc.error(err);
    return true;
  }
  return false;
};


/* Ensures that provided taskTypes are correct. */
var parseTaskTypes = function(taskTypes, rpc) {
    var taskTypesType = typeof(taskTypes),
        effTaskTypes = taskTypes;

    // Is string, undefined or array.
    if (taskTypesType === "string") {
        effTaskTypes = [taskTypes];
    } else if (taskTypesType === "undefined") {
        effTaskTypes = [];
    } else if (Array.isArray(taskTypes)) {
        rpc.error({'type': 'InvalidArgumentType', 'argumentName': 'taskTypes'});
        return null;
    }

    for (var i=0, l=effTaskTypes.length; i < l; ++i ) {
        if (effTaskTypes[i] !== null) {
            if ( checkType(rpc, effTaskTypes[i], ["taskTypes[", i, "]"].join(""), "string") )
                return null;
            if ( !taskType.hasOwnProperty(effTaskTypes[i]) ) {
                rpc.error({'type': 'UnknownTaskType', 'taskType': effTaskTypes[i],
                      'argumentName': ["taskTypes[", i, "]"].join("") });
                return null;
            }
        }
    }

    // Default if none is provided.
    if (effTaskTypes.length === 0) {
        effTaskTypes.push(taskType.fullStatistics);
    }

    return effTaskTypes;
};

var onMongodbError = function(err, client){
    this.response.error({type: 'MongoDBError', msg: err.message});
    console.log(err);
    client.close();
};

var findInDb = function() {
    var db = arguments[0];
    var collectionName = arguments[1];
    var onFinished = arguments[arguments.length-1];
    var spec = arguments.length > 3 ? arguments[2] : null;
    var fields = arguments.length > 4 ? arguments[3] : null;
    var context = this;

    var client = this.getDbClient(db);
    client.open(function(err, pClient) {
        if (err) { onMongodbError.bind(context)(err, client); return; }
        client.collection(collectionName, function(err, collection) {
            if (err) { onMongodbError.bind(context)(err, client); return; }
            collection.find(spec, fields, function(err, cursor){
                if (err) onMongodbError.bind(context)(err, client);
                else { onFinished(cursor); }
            });
        } );
    });
};


// Update documents in database.
var updateDocuments = function(db, collectionName, spec, changes, multi, onFinished) {
    var context = this;
    var client = this.getDbClient(db);
    client.open(function(err, pClient) {
        if (err) {
            onMongodbError.bind(context)(err, client);
            return;
        }
        client.collection(collectionName, function(err, collection) {
            if (err) {
                onMongodbError.bind(context)(err, client);
                return;
            }
            collection.update(spec, changes, {multi: multi}, function(err, cursor){
                if (err) {
                    onMongodbError.bind(context)(err, client);
                } else {
                    if (onFinished) onFinished();
                }
            });
        } );
    });
};


var loadProject = function(project, onFinished) {
    var fields =  {'currentFullState': 0};
    var context = this;
    findInDb.call(this, project.name, 'progresses', {}, fields, function(cursor){
        cursor.toArray(function(err, a){
            a.forEach(function(item){
                project.addJob(item);
            });
            cursor.close();
            findInDb.call(context, project.name, 'jobs', {}, {'yaml':0}, function(cursor) {
                cursor.toArray(function(err, a){
                    a.forEach(function(item){
                        var j = project.getJob(item.name);
                        j.duration = item.simulationParameters.duration;
                        j.batchLength = item.simulationParameters.batchLength;
                        j.stepDuration = item.simulationParameters.stepDuration;
                    });
                });
                cursor.close();
                cursor.db.close();
                if (onFinished) onFinished();
            });
        });
    });
};

// Checks whether specified project exists.
var projectExists = function(projectName, onExists, onNotExists) {
    var jsrpc = this.response,
        context = this;
    // Error handler.
    var onError = onMongodbError.bind(this.response);

    if (projects.hasOwnProperty(projectName)) {
        if (onExists) onExists(projects[projectName]);
    } else {
        // Try to find it in the database.
        var client = this.getDbClient(projectName);
        client.open(function(err, p_client){
            // Even if db doesn't exist there is no error. So we need to check
            // for dummy `info.project` document.
            if (err) { onError(err, client); return; }
            client.collection('info', function(err, collection){
                if (err) { onError(err, client); return; }
                collection.find({'_id': 'project'}, function(err, cursor){
                    if (err) { onError(err, client); return; }
                    cursor.count(function(err, number){
                        cursor.close();
                        if (err) { onError(err, client); return; }
                        if (number === 0) {
                            if (onNotExists) onNotExists();
                        } else if (number === 1) {
                            // Store info in cache.
                            var p = projects[projectName] = new Project(projectName);
                            loadProject.bind(context)(p, function(){
                                if (onExists) onExists(p);
                            });
                        } else {
                            jsrpc.error(
                             "Whow! Internal error: info.project has count > 1");
                        }
                        client.close();
                    });
                });
            });
        });
    }
};

// Checks whether specified job exists.
var jobExists = function(projectName, jobName, onExists, onNotExists) {
    var handleProjectExists = function(project) {
        if (project.hasJob(jobName)) {
            if (onExists) onExists(project, project.getJob(jobName));
        } else {
            if (onNotExists) onNotExists();
        }
    };
    projectExists.bind(this)(projectName, handleProjectExists, onNotExists);
};

var taskExists = function(projectName, jobName, taskType) {
    //var cur = job.currentTasks || [];
    //return cur.indexOf(taskType) !== -1;

    var mask = function(task, index) {
        return task.project === projectName && task.job === jobName
                && task.type === taskType;
    };
    if (waitingQueue.some(mask)) {
        return true;
    }
    for (var key in waitingActivation) {
        if (waitingActivation.hasOwnProperty(key)
            && mask(waitingActivation[key]) )
            return true;
    }
    return false;
};


// Types
var SchedulerContext = function(jsonRpcResponse) {
    this.response = jsonRpcResponse;
    this.server = new mongodb.Server(cfg.mongodbAddress[0], cfg.mongodbAddress[1], {});
};
SchedulerContext.prototype.getDbClient = function(projectName) {
    return new mongodb.Db(projectName, this.server, {native_parser: true});
};

var Project = function(name){
    this.name = name;
    this.jobs = {};
};
Project.prototype.hasJob = function(jobName){
    return this.jobs.hasOwnProperty(jobName);
};
Project.prototype.getJob = function(jobName){
    return this.jobs[jobName];
};
Project.prototype.addJob = function(jobInfo){
    this.jobs[jobInfo.jobname] = jobInfo;
};


// Adds required tasks to queue if required with dependency calculation.
var addTaskImplementation = function(projectName, jobName, taskTypes) {
    var handleNoJob = (function(){
        this.response.error({type: 'JobNotFound'});
    }).bind(this);
    var handleHasJob = (function(project, job){
        var getTask = function(type) {
            var a = {
                project: projectName,
                job: job.jobname,
                type: type
            };
            if (type === taskType.simulation) {
                a['startState'] = job.done;
                a['duration'] = job.duration;
                a['batchLength'] = job.batchLength;
                a['stepDuration'] = job.stepDuration;
            }
            return a;
        };

        if (job.done < job.totalSteps) {
            if (!taskExists(projectName, jobName, taskType.simulation)) {
                waitingQueue.push(getTask(taskType.simulation));
            } else {
                this.response.error({type: 'DuplicateTask',
                                    taskType:taskType.simulation});
            }
        } else if (job.fullStatistics === false) {
            // Statistics are parallel.
            if (taskExists(projectName, jobName, taskType.basicStatistics)) {
                this.response.error({type: 'DuplicateTask',
                                    taskType:taskType.basicStatistics});
                return;
            }
            if (taskExists(projectName, jobName, taskType.idleTimes) ) {
                this.response.error({type: 'DuplicateTask',
                                    taskType:taskType.idleTimes});
                return;
            }
            if (taskExists(projectName, jobName, taskType.throughput) ) {
                this.response.error({type: 'DuplicateTask',
                                    taskType:taskType.throughput});
                return;
            }

            if (job.basicStatistics === false) {
                waitingQueue.push(getTask(taskType.basicStatistics));
            }
            if (job.idleTimes === false) {
                waitingQueue.push(getTask(taskType.idleTimes));
            }
            if (job.throughtput === false) {
                waitingQueue.push(getTask(taskType.throughput));
            }
        } else {
            this.response.error({type: 'AlreadyDone'});
            return;
        }
        this.response.response('success');
    }).bind(this);
    jobExists.bind(this)(projectName, jobName, handleHasJob, handleNoJob);
};


var abortTaskImplementation = function(projectName, jobName) {
    var len = 0,
        queueLen = waitingQueue.length;
    // Clear waiting tasks.
    waitingQueue = waitingQueue.filter(function(item){
        return item.project !== projectName || item.job !== jobName;
    });
    len = queueLen - waitingQueue.length;

    // Clear waiting for activation.
    for(var key in waitingActivation){
        var val = waitingActivation[key];
        if (val.project === projectName && val.job === jobName) {
            delete waitingActivation[key];
            len += 1;
        }
    }

    this.response(len);
};


var getTasksImplementation = function(workerId, taskTypes){
    if (waitingActivation.hasOwnProperty(workerId) ||
        runningTasks.hasOwnProperty(workerId)) {
        this.response.error({type: 'WorkerHasTask'});
        return;
    }

    var task = null;
    for(var i=0, l=waitingQueue.length; i<l; ++i) {
        var it = waitingQueue[i];
        if (taskTypes.indexOf(it.type) !== -1) {
            task = it;
            delete waitingQueue[i]; // remove this task from queue
            break;
        }
    }

    if (task === null){
        task = {empty: true};
    } else {
        task['empty'] = false;
        task['databases'] = [{host: cfg.mongodbAddress[0],
                              port: cfg.mongodbAddress[1]}];
        task['lastUpdate'] = newDate();
        task['sig'] = task['lastUpdate'].toJSON();
        waitingActivation[workerId] = task;
    }
    this.response.response(task);
};


var acceptTaskImplementation = function(workerId, sig){
    if (workerId in waitingActivation) {
        var t = waitingActivation[workerId];
        if (t.sig === sig) {
            delete waitingActivation[workerId];
            runningTasks[workerId] = t;
            t.lastUpdate = new Date();
            t.sig = t.lastUpdate.toJSON();
            this.response.response({sig: t.sig});
        } else {
            this.response.error({type:'InvalidSignature'});
        }
    } else {
        this.response.error({type:'InvalidWorkerId'});
    }
};


var rejectTaskImplementation = function(workerId, sig) {
    if (workerId in waitingActivation) {
        var t = waitingActivation[workerId];
        if (t.sig === sig) {
            delete waitingActivation[workerId];
            waitingQueue.push(t);
            delete t['sig'];
            delete t['empty'];
        } else {
            this.response.error({type:'InvalidSignature'});
        }
    } else {
        this.response.error({type:'InvalidWorkerId'});
    }
};


var taskFinishedImplementation = function(workerId, sig) {
    // Check task existence.
    if (!(workerId in runningTasks)) {
        this.response.error({type:'InvalidWorkerId'});
        return;
    }

    var task = runningTasks[workerId];
    // Check signature
    if (task.sig !== sig) {
        this.response.error({type:'InvalidSignature'});
        return;
    }

    delete runningTasks[workerId];
    var job = projects[task.project][task.job];
    var dbChange = {'$set':{}};
    var dbSpec = {'_id': task.job};
    var startNext = false;
    // Store
    if (task.type === taskType.simulation) {
        job.done += job.batchLength;
        // Special case
        delete change['$set'];
        change['$inc'] = {'done': job.batchLength };
        startNext = true;
    } else if (task.type === taskType.basicStatistics) {
        job.basicStatistics = true;
        change['$set']['basicStatistics'] = true;
    } else if (task.type === taskType.idleTimes) {
        job.idleTimes = true;
        change['$set']['idleTimes'] = true;
    } else if (task.type === taskType.throughput) {
        job.throughput = true;
        change['$set']['throughput'] = true;
    }

    if (job.basicStatistics && job.idleTimes && job.throughput) {
        job.fullStatistics = true;
        change['$set']['fullStatistics'] = true;
    }

    // Update db.
    var onSuccess = function(needNext) {
        this.response.response("success");
        // Start simulation tasks
        if (needNext)
            process.nextTick(addTaskImplementation.bind(this, task.project, task.job));
    };
    updateDocuments(task.project, 'progresses', dbSpec, dbChange, false,
                    onSuccess.bind(this, startNext));
};


var taskInProgressImplementation = function(workerId, sig) {
    // Check task existence.
    if (!(workerId in runningTasks)) {
        this.response.error({type:'InvalidWorkerId'});
        return;
    }

    var task = runningTasks[workerId];
    // Check signature
    if (task.sig !== sig) {
        this.response.error({type:'InvalidSignature'});
        return;
    }

    task.lastUpdate = new Date();
    task.sig = task.lastUpdate.toJSON();
    this.response.response({'sig':task.sig});
};


var getCurrentTasksImplementation = function() {
    var result = [];
    for (var i in waitingQueue) {
        result.push(waitingQueue[i]);
    }
    for (var wid in waitingActivation) {
        if (waitingActivation.hasOwnProperty(wid)) {
            result.push({'id': wid, 'sig': waitingActivation[wid].sig});
        }
    }
    for (var wid in runningTasks) {
        if (runningTasks.hasOwnProperty(wid)) {
            result.push({'id': wid, 'sig': runningTasks[wid].sig});
        }
    }
    this.response.response(result);
};


var restartTasksImplementation = function(tasks) {
    tasks.forEach(function(task){
        // Try running tasks first, then waiting acception.
        if (task.id in runningTasks) {
            var currentTask = runningTasks[task.id];
            delete runningTasks[task.id];
            waitingQueue.push(currentTask);
        } else if (task.id in waitingActivation) {
            var currentTask = waitingActivation[task.id];
            delete runningTasks[task.id];
            waitingQueue.push(currentTask);
        }
    });
};

// RPC methods.
var hello = function(rpc){
  rpc.response("Hello! I am ControlNode on node.js");
};


var addTask = function(rpc) {
  var projectName = arguments[1],
      jobName = arguments[2];

    // Check arg types.
    if (checkType(rpc, projectName, "projectName", "string") ||
        checkType(rpc, jobName, "jobName", "string") ) {
      return;
    }

    var taskTypes = parseTaskTypes(arguments[3], rpc);
    if (taskTypes == null) return;

    var context = new SchedulerContext(rpc);
    addTaskImplementation.bind(context)(projectName, jobName, taskTypes);
};


var abortTask = function(rpc) {
    var projectName = argument[1],
        jobName = argument[2];

    if (checkType(rpc, projectName, "projectName", "string") ||
        checkType(rpc, jobName, "jobName", "string") ) {
        return;
    }

    abortTaskImplementation.bind(new SchedulerContext(rpc))(projectName, jobName);
};


var getTask = function(rpc){
    var taskTypes = parseTaskTypes(arguments[1], rpc);
    if (taskTypes == null) return;
    getTasksImplementation.call(new SchedulerContext(rpc), taskTypes);
};


var acceptTask = function(rpc, workerId, sig){
    if (checkType(rpc, workerId, "workerId", "string") ||
        checkType(rpc, sig, "sig", "string") ) {
        return;
    }
    acceptTaskImplementation.call(new SchedulerContext(rpc), workerId, sig);
};


var rejectTask = function(rpc, workerId, sig) {
    if (checkType(rpc, workerId, "workerId", "string") ||
        checkType(rpc, sig, "sig", "string") ) {
        return;
    }
    rejectTaskImplementation.call(new SchedulerContext(rpc), workerId, sig);
};


var taskFinished = function(rpc, workerId, sig){
    if (checkType(rpc, workerId, "workerId", "string") ||
        checkType(rpc, sig, "sig", "string") ) {
        return;
    }
    taskFinished.call(new SchedulerContext(rpc), workerId, sig);
};


var taskInProgress = function(rpc, workerId, sig){
    if (checkType(rpc, workerId, "workerId", "string") ||
        checkType(rpc, sig, "sig", "string") ) {
        return;
    }
    taskInProgress.call(new SchedulerContext(rpc), workerId, sig);
};


var getCurrentTasks = function(rpc) {
    getCurrentTasksImplementation.call(new SchedulerContext(rpc));
};

var restartTasks = function(rpc, tasks) {
    if (!Array.isArray(tasks)) {
        rpc.error({'type':'InvalidArgumentType', 'argumentName': 'tasks'});
        return;
    }
    tasks.forEach(function(item, index){
        if (!('id' in item) || !('sig' in item)) {
            rpc.error({'type':'InvalidArgumentType',
                      'argumentName': 'tasks['+index+']'});
            return;
        }
    });

    restartTasksImplementation.call(new SchedulerContext(rpc), tasks);
};

exports.rpcMethods = {'hello':hello, 'addTask':addTask, 'abortTask':abortTask,
    'getTask': getTask, 'acceptTask': acceptTask, 'rejectTask': rejectTask,
    'taskFinished': taskFinished, 'taskInProgress': taskInProgress,
    'getCurrentTasks': getCurrentTasks, 'restartTasks': restartTasks
};
exports.cfg = cfg;
// exports.taskType = taskType;
