var SchedulerLib = require('../jslib/scheduler');

// Scheduler constants
var taskType = SchedulerLib.taskTypes;


// Module locals
var cfg = {};
var scheduler = new SchedulerLib.Scheduler();


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


// Types
var SchedulerContext = function(jsonRpcResponse) {
    this.response = jsonRpcResponse;
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
    
    scheduler.addTask(rpc, projectName, jobName, taskTypes);
    // var context = new SchedulerContext(rpc);
    // addTaskImplementation.bind(context)(projectName, jobName, taskTypes);
};


var abortTask = function(rpc, projectName, jobName) {
    if (checkType(rpc, projectName, "projectName", "string") ||
        checkType(rpc, jobName, "jobName", "string") ) {
        return;
    }

    scheduler.abortTask(rpc, projectName, jobName);
};


var getTask = function(rpc, workerId){
    if (checkType(rpc, workerId, "workerId", "string")) {
        return;
    }
    var taskTypes = parseTaskTypes(arguments[2], rpc);
    if (taskTypes === null) return;
    scheduler.getTask(rpc, workerId, taskTypes);
};


var acceptTask = function(rpc, workerId, sig){
    if (checkType(rpc, workerId, "workerId", "string") ||
        checkType(rpc, sig, "sig", "string") ) {
        return;
    }
    scheduler.acceptTask(rpc, workerId, sig);
};


var rejectTask = function(rpc, workerId, sig) {
    if (checkType(rpc, workerId, "workerId", "string") ||
        checkType(rpc, sig, "sig", "string") ) {
        return;
    }
    scheduler.rejectTask(rpc, workerId, sig);
};


var taskFinished = function(rpc, workerId, sig){
    if (checkType(rpc, workerId, "workerId", "string") ||
        checkType(rpc, sig, "sig", "string") ) {
        return;
    }
    scheduler.taskFinished(rpc, workerId, sig);
};


var taskInProgress = function(rpc, workerId, sig){
    if (checkType(rpc, workerId, "workerId", "string") ||
        checkType(rpc, sig, "sig", "string") ) {
        return;
    }
    scheduler.taskInProgress(rpc, workerId, sig);
};


var getCurrentTasks = function(rpc) {
    scheduler.getCurrentTasks(rpc);
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

    scheduler.restartTasks(rpc, tasks);
};


exports.rpcMethods = {'hello':hello, 'addTask':addTask, 'abortTask':abortTask,
    'getTask': getTask, 'acceptTask': acceptTask, 'rejectTask': rejectTask,
    'taskFinished': taskFinished, 'taskInProgress': taskInProgress,
    'getCurrentTasks': getCurrentTasks, 'restartTasks': restartTasks
};
exports.cfg = cfg;
