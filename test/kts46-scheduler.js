var vows = require('vows'),
    assert = require('assert'),
    fs = require('fs'),
    http = require('http');

var options = {
  host: 'localhost',
  port: 46212,
  path: '/jsonrpc',
  method: 'POST'
};

var callServer = function(method, params, cbk) {
  var req = http.request(options, function(res) {
    res.setEncoding('utf8');
    res.on('data', function (chunk) {
      //console.log(chunk);
      // console.log(JSON.parse(chunk));
      cbk(JSON.parse(chunk));
    });
  });
  // write data to request body
  req.write(JSON.stringify({method: method, params:params,
                           id: Math.floor(Math.random()*10000)}));
  req.end();
};

// Macroses
var assertArgTypeInvalid = function(r, e) {
    return assertArgInvalid("InvalidArgumentType");
};
var assertArgInvalid = function(errorName){
    return function(r, e) {
        assert.isNotNull(r.error);
        assert.strictEqual(r.error.type, errorName);
    };
};
var assertHasError = function(r, e) {
    assert.isNull(r.result);
    assert.isNotNull(r.error);
};
var assertErrorArgName = function(argName) {
    return function(r, e) {
        assert.isNotNull(r.error);
        assert.strictEqual(r.error.argumentName, argName);
    };
};


vows.describe('Division by Zero').addBatch({
    "when calling hello": {
        topic: function(){callServer("hello", [], this.callback);},
        "must return string": function(response, e) {
          assert.isString(response.result);
          assert.isNull(response.error);
        }
    },
    "when calling addTask": {
        "with invalid project name": {
            topic: function(){callServer("addTask", [11, "j1"],this.callback);},
            "InvalidTypeArgument must be raised": assertArgTypeInvalid,
            "result must be null": assertHasError,
            "argument name must be projectName": assertErrorArgName("projectName")
        },
        "with null project name": {
            topic: function(){callServer("addTask", [null, "j1"],this.callback);},
            "InvalidTypeArgument must be raised": assertArgTypeInvalid,
            "result must be null": assertHasError,
            "argument name must be projectName": assertErrorArgName("projectName")
        },
        "with invalid job name": {
            topic: function(){callServer("addTask", ["p1", 1], this.callback);},
            "InvalidTypeArgument must be raised": assertArgTypeInvalid,
            "result must be null": assertHasError,
            "argument name must be jobName": assertErrorArgName("jobName")
        },
        "with null job name": {
            topic: function(){callServer("addTask", ["p1", null], this.callback);},
            "InvalidTypeArgument must be raised": assertArgTypeInvalid,
            "result must be null": assertHasError,
            "argument name must be jobName": assertErrorArgName("jobName")
        },
        "with invalid task type type": {
            topic: function(){
                callServer("addTask", ["p1", "j1", ["idleTimes", null, 1] ], this.callback);},
            "InvalidTypeArgument must be raised": assertArgTypeInvalid,
            "result must be null": assertHasError,
            "argument name must be taskTypes": assertErrorArgName("taskTypes[2]")
        },
        "with unknown task type": {
            topic: function(){
                callServer("addTask", ["p1", "j1",["simulation", "lalla"] ],
                           this.callback);
            },
            "UnknownTaskType must be raised": assertArgInvalid("UnknownTaskType"),
            "result must be null": assertHasError,
            "argument name must be taskTypes": assertErrorArgName("taskTypes[1]"),
            "taskType must be lalla": function(r, e) {
                assert.isNotNull(r.error);
                assert.strictEqual(r.error.taskType, "lalla");
            }
        },
        "for project that doesn't exist": {
            topic: function() {
                callServer("addTask", ["QQA123", "exp_1_9-s4"], this.callback);
            },
            "there must be JobNotFound": function(r, e) {
                assert.isNull(r.result);
                assert.isNotNull(r.error);
                assert.strictEqual(r.error.type, 'JobNotFound');
            }
        },
        "for job that doesn't exist": {
            topic: function() {
                callServer("addTask", ["exp_3", "QQQSDFSDFq3498"], this.callback);
            },
            "there must be JobNotFound": function(r, e) {
                assert.isNull(r.result);
                assert.isNotNull(r.error);
                assert.strictEqual(r.error.type, 'JobNotFound');
            }
        },
        "with valid args for done task": {
            topic: function() {
                callServer("addTask", ["exp_3", "exp_1_9-s4"], this.callback);
            },
            "there must be AlreadyDone": function(r, e) {
                assert.isNull(r.result);
                assert.isNotNull(r.error);
                assert.strictEqual(r.error.type, 'AlreadyDone');
            }
        }
    }
}).export(module);
//}).run();
