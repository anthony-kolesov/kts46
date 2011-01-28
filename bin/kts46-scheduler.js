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
    } else if (!taskTypes.hasOwnProperty("length")) {
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
        if (err) onMongodbError.bind(context)(err, client);
        client.collection(collectionName, function(err, collection) {
            if (err) onMongodbError.bind(context)(err, client);
            else {
                collection.find(spec, fields, function(err, cursor){
                    if (err) onMongodbError.bind(context)(err, client);
                    else {
                        onFinished(cursor);
                    }
                });
            }
        } );
    });
};

var loadProject = function(project, onFinished) {
    var fields =  {'currentFullState': 0};
    findInDb.bind(this)(project.name, 'progresses', {}, fields, function(cursor){
        cursor.toArray(function(err, a){
            a.forEach(function(item){
                project.addJob(item);
            });
            cursor.close();
            cursor.db.close();
            if (onFinished) onFinished();
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

var taskExists = function(job, taskType) {
    var cur = job.currentTasks || [];
    return cur.indexOf(taskType) !== -1;
};


// Types
var SchedulerContext = function(jsonRpcResponse) {
    this.response = jsonRpcResponse;
    this.server = new mongodb.Server(cfg.mongodbAddress[0], cfg.mongodbAddress[1], {});
};
SchedulerContext.prototype.getDbClient = function(projectName) {
    return new mongodb.Db(projectName, this.server);
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
    jobInfo.currentTasks = [];
};


// Adds required tasks to queue if required with dependency calculation.
var addTaskImplementation = function(projectName, jobName, taskTypes) {
    var handleNoJob = (function(){
        this.response.error({type: 'JobNotFound'});
    }).bind(this);
    var handleHasJob = (function(project, job){
        var getTask = function(type) {
            return {
                project: projectName,
                job: job.jobname,
                taskType: type
            };
        };

        if (job.done < job.totalStep) {
            if (!taskExists(job, taskType.simulation)) {
                waitingQueue.push(getTask(taskType.simulation));
                job.currentTasks.push(taskType.simulation);
            } else {
                this.response.error({type: 'DuplicateTask',
                                    taskType:taskType.simulation});
            }
        } else if (job.fullStatistics === false) {
            // Statistics are parallel.
            if (taskExists(job, taskType.basicStatistics)) {
                this.response.error({type: 'DuplicateTask',
                                    taskType:taskType.basicStatistics});
                return;
            }
            if (taskExists(job, taskType.idleTimes) ) {
                this.response.error({type: 'DuplicateTask',
                                    taskType:taskType.idleTimes});
                return;
            }
            if (taskExists(job, taskType.throughput) ) {
                this.response.error({type: 'DuplicateTask',
                                    taskType:taskType.throughput});
                return;
            }

            if (job.basicStatistics === false) {
                waitingQueue.push(getTask(taskType.basicStatistics));
                job.currentTasks.push(taskType.basicStatistics);
            }
            if (job.idleTimes === false) {
                waitingQueue.push(getTask(taskType.idleTimes));
                job.currentTasks.push(taskType.idleTimes);
            }
            if (job.throughtput === false) {
                waitingQueue.push(getTask(taskType.throughput));
                job.currentTasks.push(taskType.throughput);
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
    var len = 0;
    if (projects.hasOwnProperty(projectName)){
        var p = projects[projectName];
        if (p.hasJob(jobName)) {
            var j = p.getJob(joibName);
            len = j.currentTasks.length;
            if (len > 0) {
                waitingQueue = waitingQueue.filter(function(item){
                    return item.project !== projectName || item.job !== jobName;
                });
                j.currentTasks = [];
            }
        }
    }
    this.response(len);
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

exports.rpcMethods = {hello: hello, addTask: addTask};
exports.cfg = cfg;
// exports.taskType = taskType;
