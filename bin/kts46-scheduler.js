var mongodb = require('../jslib/mongodb'),
    fluentMongodb = require('../jslib/mongodb-fluent'),
    ProjectStorage = require('../jslib/projectStorage').Storage;

// Scheduler constants
var taskType = { simulation: "simulation", basicStatistics: "basicStatistics",
  idleTimes: "idleTimes", throughput: "throughput",
  fullStatistics: "fullStatistics"
};


var getDbServer = function() {
    var mongodbAddress = ['192.168.1.5', 27017];
    return new mongodb.Server(mongodbAddress[0], mongodbAddress[1], {});
};

// Module locals
var waitingQueue = [];
var waitingActivation = {};
var runningTasks = {};
//var projects = {};
var cfg = {};
var projectStorage = new ProjectStorage(getDbServer());


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
    var effTaskTypes = taskTypes;

    // Is string, undefined or array.
    if (typeof(taskTypes) === "undefined") {
        effTaskTypes = [];
    } else if (!Array.isArray(taskTypes)) {
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

    return effTaskTypes;
};

var onMongodbError = function(err, client){
    this.response.error({type: 'MongoDBError', msg: err.message});
    console.log(err);
    client.close();
};
var onMongodbError2 = function(rpc, err){
    rpc.error({type: 'MongoDBError', msg: err.message});
    console.log(err);
};

/*var loadProject = function(project, onFinished) {
    var fields =  {'currentFullState': 0};
    var context = this;
    var client = context.getDbClient(project.name);
    fluentMongodb.find(client, 'progresses', {}, fields, function(cursor){
        cursor.toArray(function(err, a){
            a.forEach(function(item, index, array){
                var j = {
                    '_id': item._id,
                    'fullStatistics': item.fullStatistics,
                    'done': item.done,
                    'totalSteps': item.totalSteps,
                    'batches': item.batches,
                    'jobname': item.jobname,
                    'basicStatistics': item.basicStatistics,
                    'idleTimes': item.idleTimes,
                    'throughput': item.throughput
                };
                project.addJob(j);
                if (index === array.length - 1) {
                    cursor.close();
                    client.close();
                    var client2 = context.getDbClient(project.name);
                    fluentMongodb.find(client2, 'jobs', {}, {'yaml':0}, function(cursor2) {
                        cursor2.toArray(function(err, a){
                            a.forEach(function(item, index, array){
                                var j = project.getJob(item.name);
                                j.duration = item.simulationParameters.duration;
                                j.batchLength = item.simulationParameters.batchLength;
                                j.stepDuration = item.simulationParameters.stepDuration;
                                // Last
                                if (index === array.length - 1) {
                                    cursor2.close();
                                    client2.close();
                                    if (onFinished) onFinished();
                                }
                            });
                        });
                    }, onMongodbError.bind({}, this.response) );
                }
            });
        });
    }, onMongodbError.bind({}, this.response));
};*/

// Checks whether specified project exists.
/*var projectExists = function(projectName, onExists, onNotExists) {
    var jsrpc = this.response,
        context = this;
    // Error handler.
    var onError = onMongodbError.bind(this.response);

    if (projects.hasOwnProperty(projectName)) {
        if (onExists) onExists(projects[projectName]);
    } else {
        // Try to find it in the database.
        var client = this.getDbClient(projectName);
        fluentMongodb.find(client, 'info', {'_id': 'project'}, {}, function(cursor){
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
        }, onMongodbError2.bind(context));
    }
};*/

// Checks whether specified job exists.
/*var jobExists = function(projectName, jobName, onExists, onNotExists) {
    var handleProjectExists = function(project) {
        if (project.hasJob(jobName)) {
            if (onExists) onExists(project, project.getJob(jobName));
        } else {
            if (onNotExists) onNotExists();
        }
    };
    projectExists.bind(this)(projectName, handleProjectExists, onNotExists);
};*/

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
    this.server = getDbServer();
};
SchedulerContext.prototype.getDbClient = function(projectName) {
    return new mongodb.Db(projectName, this.server, {native_parser: true});
};

/*var Project = function(name){
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
*/

// Adds required tasks to queue if required with dependency calculation.
var addTaskImplementation = function(projectName, jobName, taskTypes) {
    // var handleNoJob = (function(){
        // this.response.error({type: 'JobNotFound'});
    // }).bind(this);
    var handleHasJob = (function(job){

        if (job === null) {
            this.response.error({type: 'JobNotFound'});
            return;
        }

        var getTask = function(type) {
            var a = {
                project: projectName,
                job: job.id,
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

    projectStorage.getJob(projectName, jobName, handleHasJob, onMongodbError2.bind(this.response));
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
    this.response.response(len);
};


var getTaskImplementation = function(workerId, taskTypes){
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
            waitingQueue.splice(i, 1);
        }
    }

    if (task === null){
        task = {empty: true};
    } else {
        task['empty'] = false;
        task['databases'] = [{host: cfg.mongodbAddress[0],
                              port: cfg.mongodbAddress[1]}];
        task['lastUpdate'] = new Date();
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
            this.response.response("success");
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
    var startNext = false;
    if (task.type === taskType.simulation) {
        startNext = true;
    }

    if (startNext)
        process.nextTick(addTaskImplementation.bind(this, task.project, task.job));
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
    //for (var i in waitingQueue) {
    //    result.push(waitingQueue[i]);
    //}
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
    var restarted = 0;
    tasks.forEach(function(task){
        // Try running tasks first, then waiting acception.
        if (task.id in runningTasks) {
            var currentTask = runningTasks[task.id];
            delete runningTasks[task.id];
            waitingQueue.push(currentTask);
            restarted += 1;
        } else if (task.id in waitingActivation) {
            var currentTask = waitingActivation[task.id];
            delete waitingActivation[task.id];
            waitingQueue.push(currentTask);
            restarted += 1;
        }
    });
    this.response.response({'restarted': restarted});
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


var abortTask = function(rpc, projectName, jobName) {
    if (checkType(rpc, projectName, "projectName", "string") ||
        checkType(rpc, jobName, "jobName", "string") ) {
        return;
    }

    abortTaskImplementation.bind(new SchedulerContext(rpc))(projectName, jobName);
};


var getTask = function(rpc, workerId){
    if (checkType(rpc, workerId, "workerId", "string")) {
        return;
    }
    var taskTypes = parseTaskTypes(arguments[2], rpc);
    if (taskTypes === null) return;
    getTaskImplementation.call(new SchedulerContext(rpc), workerId, taskTypes);
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
    taskFinishedImplementation.call(new SchedulerContext(rpc), workerId, sig);
};


var taskInProgress = function(rpc, workerId, sig){
    if (checkType(rpc, workerId, "workerId", "string") ||
        checkType(rpc, sig, "sig", "string") ) {
        return;
    }
    taskInProgressImplementation.call(new SchedulerContext(rpc), workerId, sig);
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
