var RPCClient = require('../jslib/jsonrpc-client').Client,
    callServer = require('../jslib/jsonrpc-client').callServer,
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

var getClient = function() {
    return new RPCClient('192.168.1.2', 46212);
}
var client = getClient();

// Locals
var existingProject = 'node_test',
    existingJobDone = 'node_test_done',
    existingJobUndone = 'undone',
    unexistingProject = 'QQQSDFSDFq3498',
    unexistingJob = 'QQQSDFSDFq3498sfsdf';

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
};

client.call('hello', onHello);
