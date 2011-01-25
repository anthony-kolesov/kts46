// Scheduler constants
var taskType = { simulation: "simulation", basicStatistics: "basicStatistics",
  idleTimes: "idleTimes", throughput: "throughput",
  fullStatistics: "fullStatistics"
};

// Util methods.
var checkType = function(rpc, arg, argname, type) {
  if (typeof(arg) !== type) {
    var err = {"type": "InvalidArgumentType", "argumentName": argname};
    rpc.error(err);
    return true;
  }
  return false;
};

// RPC methods.
var hello = function(rpc){
  rpc.response("Hello! I am ControlNode on node.js");
};

var addTask = function(rpc) {
  var projectName = arguments[1],
      jobName = arguments[2],
      taskTypes = arguments[3];

  // Check arg types.
  if (checkType(rpc, projectName, "projectName", "string") ||
      checkType(rpc, jobName, "jobName", "string") ) {
    return;
  }

  rpc.response("Adding task: " + projectName + "." + jobName + " type: " + taskTypes);
}


exports.rpcMethods = {hello: hello, addTask: addTask};
// exports.taskType = taskType;
