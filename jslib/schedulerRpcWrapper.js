var SchedulerLib = require('./scheduler');

// Scheduler constants
var taskType = SchedulerLib.taskTypes;


var Wrapper = function() {
    this.scheduler = new SchedulerLib.Scheduler();
};


// Util methods.
Wrapper.prototype._checkType = function(rpc, arg, argname, type) {
    if (typeof(arg) !== type) {
        var err = {"type": "InvalidArgumentType", "argumentName": argname};
        rpc.error(err);
        return true;
    }
    return false;
};


/* Ensures that provided taskTypes are correct. */
Wrapper.prototype._parseTaskTypes = function(taskTypes, rpc) {
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
            if ( this._checkType(rpc, effTaskTypes[i], ["taskTypes[", i, "]"].join(""), "string") )
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


// RPC methods.
Wrapper.prototype.hello = function(rpc){
    rpc.response("Hello! I am ControlNode on node.js");
};


Wrapper.prototype.addTask = function(rpc) {
  var projectName = arguments[1],
      jobName = arguments[2];

    // Check arg types.
    if (this._checkType(rpc, projectName, "projectName", "string") ||
        this._checkType(rpc, jobName, "jobName", "string") ) {
      return;
    }

    var taskTypes = this._parseTaskTypes(arguments[3], rpc);
    if (taskTypes == null) return;
    
    this.scheduler.addTask(rpc, projectName, jobName, taskTypes);
};


Wrapper.prototype.abortTask = function(rpc, projectName, jobName) {
    if (this._checkType(rpc, projectName, "projectName", "string") ||
        this._checkType(rpc, jobName, "jobName", "string") ) {
        return;
    }

    this.scheduler.abortTask(rpc, projectName, jobName);
};


Wrapper.prototype.getTask = function(rpc, workerId){
    if (this._checkType(rpc, workerId, "workerId", "string")) {
        return;
    }
    var taskTypes = this._parseTaskTypes(arguments[2], rpc);
    if (taskTypes === null) return;
    this.scheduler.getTask(rpc, workerId, taskTypes);
};


Wrapper.prototype.acceptTask = function(rpc, workerId, sig){
    if (this._checkType(rpc, workerId, "workerId", "string") ||
        this._checkType(rpc, sig, "sig", "string") ) {
        return;
    }
    this.scheduler.acceptTask(rpc, workerId, sig);
};


Wrapper.prototype.rejectTask = function(rpc, workerId, sig) {
    if (this._checkType(rpc, workerId, "workerId", "string") ||
        this._checkType(rpc, sig, "sig", "string") ) {
        return;
    }
    this.scheduler.rejectTask(rpc, workerId, sig);
};


Wrapper.prototype.taskFinished = function(rpc, workerId, sig){
    if (this._checkType(rpc, workerId, "workerId", "string") ||
        this._checkType(rpc, sig, "sig", "string") ) {
        return;
    }
    this.scheduler.taskFinished(rpc, workerId, sig);
};


Wrapper.prototype.taskInProgress = function(rpc, workerId, sig){
    if (this._checkType(rpc, workerId, "workerId", "string") ||
        this._checkType(rpc, sig, "sig", "string") ) {
        return;
    }
    this.scheduler.taskInProgress(rpc, workerId, sig);
};


Wrapper.prototype.getCurrentTasks = function(rpc) {
    this.scheduler.getCurrentTasks(rpc);
};

Wrapper.prototype.restartTasks = function(rpc, tasks) {
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

    this.scheduler.restartTasks(rpc, tasks);
};

exports.Wrapper = Wrapper;
/*exports.rpcMethods = {'hello':hello, 'addTask':addTask, 'abortTask':abortTask,
    'getTask': getTask, 'acceptTask': acceptTask, 'rejectTask': rejectTask,
    'taskFinished': taskFinished, 'taskInProgress': taskInProgress,
    'getCurrentTasks': getCurrentTasks, 'restartTasks': restartTasks
};
exports.cfg = cfg;*/
