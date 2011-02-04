var RPCClient = require('../jslib/jsonrpc-client').Client,
    assert = require('assert');

// Setup assert.
assert.isString = function(value, msg) {
    assert.ok(typeof(value) === "string", msg)
};
assert.isNull = function(val, msg) {
    assert.strictEqual(val, null, msg);
};
assert.isNotNull = function(val, msg) {
    assert.notStrictEqual(val, null, msg);
};
assert.RPCHasNoError = function(rpc) {
    if (rpc.error) {console.log(rpc);}
    assert.strictEqual(rpc.error, null);
};

var getClient = function() {
    return new RPCClient('192.168.1.2', 46212);
}
var client = getClient();

// Locals
var existingProject = 'node_test',
    existingJobDone = 'node_test_done',
    existingJobUndone = 'undone',
    unexistingProject = 'QQQSDFSDFq3498',
    unexistingJob = 'QQQSDFSDFq3498sfsdf',
    wid = "test-wid";

var onHello = function(data) {
    assert.isNull(data.error, "There mustn't be errors.");
    assert.isString(data.result, "Return result must be string.");
    process.nextTick(startAddTask);
};


var startAddTask = function() {
    client.call('addTask', existingProject, existingJobUndone, onTaskAdded);
};
var onTaskAdded = function(data) {
    assert.isNull(data.error);
    assert.strictEqual(data.result, "success");
    process.nextTick(addTaskAgain);
};
var addTaskAgain = function() {
    client.call('addTask', existingProject, existingJobUndone, onTaskAddedDuplicate);
};
var onTaskAddedDuplicate = function(data) {
    assert.isNotNull(data.error);
    assert.isNull(data.result);
    assert.strictEqual(data.error.type, 'DuplicateTask');
    abortTaskUnknown();
};
var abortTaskUnknown = function() {
    client.call("abortTask", existingProject, existingJobDone, onAbortUnknownTask);
};
var onAbortUnknownTask = function(data) {
    assert.RPCHasNoError(data);
    assert.strictEqual(0, data.result);
    abortTaskKnown();
};
var abortTaskKnown = function() {
    client.call("abortTask", existingProject, existingJobUndone, onAbortKnownTask);
};
var onAbortKnownTask = function(data) {
    assert.RPCHasNoError(data);
    assert.strictEqual(1, data.result);
    abortTaskKnownAgain();
};
var abortTaskKnownAgain = function() {
    client.call("abortTask", existingProject, existingJobUndone, onAbortKnownTaskAgain);
};
var onAbortKnownTaskAgain = function(data) {
    assert.RPCHasNoError(data);
    assert.strictEqual(0, data.result);
    returnTaskToDo();
};
var returnTaskToDo = function() {
    client.call("addTask", existingProject, existingJobUndone, getTask);
};
var getTask = function() {
    client.call("getTask", wid, ['simulation', 'idleTimes'], onHasTask);
};
var onHasTask = function(data) {
    assert.RPCHasNoError(data);
    assert.strictEqual(false, data.result.empty);
    global.task = data.result;
    client.call("getTask", wid, ['simulation', 'idleTimes'], onHasTaskAlready);
};
var onHasTaskAlready = function(data) {
    assert.isNull(data.result);
    assert.isNotNull(data.error);
    assert.strictEqual(data.error.type, "WorkerHasTask");
    rejectTaskWithInvalidWid();
};
var rejectTaskWithInvalidWid = function() {
    client.call("rejectTask", wid+'adasdsad', global.task.sig, onRejectWithInvalidWid);
};
var onRejectWithInvalidWid = function(data) {
    assert.isNull(data.result);
    assert.strictEqual(data.error.type, 'InvalidWorkerId');
    rejectTaskWithInvalidSig();
};
var rejectTaskWithInvalidSig = function() {
    client.call("rejectTask", wid, global.task.sig + 'asdasd', onRejectWithInvalidSig);
};
var onRejectWithInvalidSig = function(data) {
    assert.isNull(data.result);
    assert.strictEqual(data.error.type, 'InvalidSignature');
    rejectTaskValid();
};
var rejectTaskValid = function() {
    client.call("rejectTask", wid, global.task.sig, onRejectValid);
};
var onRejectValid = function(data) {
    assert.isNull(data.error);
    assert.strictEqual(data.result, "success");
    regetTask();
};
var regetTask = function() {
    client.call("getTask", wid, ['simulation', 'idleTimes'], onHasTaskAgain);
};
var onHasTaskAgain = function(data) {
    assert.RPCHasNoError(data);
    assert.strictEqual(false, data.result.empty);
    global.task = data.result;
    acceptTaskWithInvalidWid();
};
var acceptTaskWithInvalidWid = function() {
    client.call("acceptTask", wid+'adasdsad', global.task.sig, onAcceptWithInvalidWid );
};
var onAcceptWithInvalidWid = function(data) {
    assert.isNull(data.result);
    assert.strictEqual(data.error.type, 'InvalidWorkerId');
    acceptTaskWithInvalidSig();
};
var acceptTaskWithInvalidSig = function() {
    client.call("acceptTask", wid, global.task.sig + 'asdasd', onAcceptWithInvalidSig);
};
var onAcceptWithInvalidSig = function(data) {
    assert.isNull(data.result);
    assert.strictEqual(data.error.type, 'InvalidSignature');
    acceptTaskValid();
};
var acceptTaskValid = function() {
    client.call("acceptTask", wid, global.task.sig, onAcceptValid);
};
var onAcceptValid = function(data) {
    assert.isNull(data.error);
    assert.isString(data.result.sig);
    global.task.sig = data.result.sig;
    taskInProgressWithInvalidWid();
};

var taskInProgressWithInvalidWid = function() {
    client.call("taskInProgress", wid+'adasdsad', global.task.sig, onTaskInProgressWithInvalidWid);
};
var onTaskInProgressWithInvalidWid = function(data) {
    assert.isNull(data.result);
    assert.strictEqual(data.error.type, 'InvalidWorkerId');
    taskInProgressWithInvalidSig();
};
var taskInProgressWithInvalidSig = function() {
    client.call("taskInProgress", wid, global.task.sig + 'asdasd', onTaskInProgressWithInvalidSig);
};
var onTaskInProgressWithInvalidSig = function(data) {
    assert.isNull(data.result);
    assert.strictEqual(data.error.type, 'InvalidSignature');
    taskInProgressTaskValid();
};
var taskInProgressTaskValid = function() {
    client.call("taskInProgress", wid, global.task.sig, onTaskInProgressValid);
};
var onTaskInProgressValid = function(data) {
    assert.isNull(data.error);
    assert.isString(data.result.sig);
    global.task.sig = data.result.sig;
    taskFinishedWithInvalidWid();
};


var taskFinishedWithInvalidWid = function() {
    client.call("taskFinished", wid+'adasdsad', global.task.sig, onTaskFinishedWithInvalidWid);
};
var onTaskFinishedWithInvalidWid = function(data) {
    assert.isNull(data.result);
    assert.strictEqual(data.error.type, 'InvalidWorkerId');
    taskFinishedWithInvalidSig();
};
var taskFinishedWithInvalidSig = function() {
    client.call("taskFinished", wid, global.task.sig + 'asdasd', onTaskFinishedWithInvalidSig);
};
var onTaskFinishedWithInvalidSig = function(data) {
    assert.isNull(data.result);
    assert.strictEqual(data.error.type, 'InvalidSignature');
    taskFinishedValid();
};
var taskFinishedValid = function(){
    client.call("taskFinished", wid, global.task.sig, onTaskFinishedValid);
};
var onTaskFinishedValid = function(data) {
    assert.isNull(data.error);
    assert.strictEqual(data.result, "success");
    getCurrentTasksNothing();
};

var getCurrentTasksNothing = function() {
    client.call("getCurrentTasks", onGetCurrentTasksNothing);
};
var onGetCurrentTasksNothing = function(data) {
    assert.isNull(data.error);
    assert.ok(Array.isArray(data.result));
    assert.strictEqual(data.result.length, 0);
    regetTask2();
};

var regetTask2 = function() {
    client.call("getTask", wid, ['simulation', 'idleTimes'], onHasTaskAgain2);
};
var onHasTaskAgain2 = function(data) {
    assert.strictEqual(false, data.result.empty);
    global.task = data.result;
    //assert.strictEqual(data.result.type, "idleTimes");
    getCurrentTasks();
};

var getCurrentTasks = function() {
    client.call("getCurrentTasks", onGetCurrentTasks);
};
var onGetCurrentTasks = function(data) {
    assert.isNull(data.error);
    assert.ok(Array.isArray(data.result));
    assert.strictEqual(data.result.length, 1);
    assert.strictEqual(data.result[0].id, wid);
    assert.strictEqual(data.result[0].sig, global.task.sig);
    restartTasks();
};

var restartTasks = function() {
    client.call("restartTasks", [{'id':wid, 'sig':global.task.sig}], onRestartTasks);
};
var onRestartTasks = function(data) {
    assert.isNull(data.error);
    assert.strictEqual(data.result.restarted, 1);
    getCurrentTasksAgainNothing();
};


var getCurrentTasksAgainNothing = function() {
    client.call("getCurrentTasks", onGetCurrentTasksAgainNothing);
};
var onGetCurrentTasksAgainNothing = function(data) {
    assert.isNull(data.error);
    assert.ok(Array.isArray(data.result));
    assert.strictEqual(data.result.length, 0);
    regetTask3();
};

var regetTask3 = function() {
    client.call("getTask", wid, ['simulation', 'idleTimes'], onHasTaskAgain3);
};
var onHasTaskAgain3 = function(data) {
    assert.strictEqual(false, data.result.empty);
    global.task = data.result;
    // assert.strictEqual(data.result.type, "idleTimes");
};

client.call('hello', onHello);
