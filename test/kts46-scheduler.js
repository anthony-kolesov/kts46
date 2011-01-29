var vows = require('vows'),
    assert = require('assert'),
    http = require('http');

var options = {
  host: 'localhost',
  port: 46212,
  path: '/jsonrpc',
  method: 'POST'
};

var existingProject = 'node_test',
    existingJob = 'node_test_done',
    existingJobDone = 'node_test_done',
    existingJobUndone = 'undone',
    unexistingProject = 'QQQSDFSDFq3498',
    unexistingJob = 'QQQSDFSDFq3498sfsdf';

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
    return assertHasError("InvalidArgumentType");
};
var assertHasError = function(errorName){
    return function(r, e) {
        assert.isNotNull(r.error);
        assert.strictEqual(r.error.type, errorName);
    };
};
var assertNoResult = function(r, e) {
    assert.isNull(r.result);
};
var assertErrorArgName = function(argName) {
    return function(r, e) {
        assert.isNotNull(r.error);
        assert.strictEqual(r.error.argumentName, argName);
    };
};

var resultIsSuccess = function(r, e) {
    // console.log(arguments);
    // var r = arguments['0'];
    assert.strictEqual(r.result, "success");
};

var assertNoError = function(r, e) {
    assert.isNull(r.error);
};

vows.describe('ktds46 Control node scheduler').addBatch({

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
            "result must be null": assertNoResult,
            "argument name must be projectName": assertErrorArgName("projectName")
        },
        "with null project name": {
            topic: function(){callServer("addTask", [null, "j1"],this.callback);},
            "InvalidTypeArgument must be raised": assertArgTypeInvalid,
            "result must be null": assertNoResult,
            "argument name must be projectName": assertErrorArgName("projectName")
        },
        "with invalid job name": {
            topic: function(){callServer("addTask", ["p1", 1], this.callback);},
            "InvalidTypeArgument must be raised": assertArgTypeInvalid,
            "result must be null": assertNoResult,
            "argument name must be jobName": assertErrorArgName("jobName")
        },
        "with null job name": {
            topic: function(){callServer("addTask", ["p1", null], this.callback);},
            "InvalidTypeArgument must be raised": assertArgTypeInvalid,
            "result must be null": assertNoResult,
            "argument name must be jobName": assertErrorArgName("jobName")
        },

        "for project that doesn't exist": {
            topic: function() {
                callServer("addTask", [unexistingProject, existingJob], this.callback);
            },
            "there mustn't be result": assertNoResult,
            "there ust be JobNotFound": assertHasError("JobNotFound")
        },

        "for job that doesn't exist": {
            topic: function() {
                callServer("addTask", [existingProject, unexistingJob], this.callback);
            },
            "there mustn't be result": assertNoResult,
            "there ust be JobNotFound": assertHasError("JobNotFound")
        },

        "with valid args for done task": {
            topic: function() {
                callServer("addTask", [existingProject, existingJobDone],
                           this.callback);
            },
            "there mustn't be result": assertNoResult,
            "there ust be AlreadyDone": assertHasError("AlreadyDone")
        },

        "for undone task": {
            topic: function() {
                callServer("addTask", [existingProject, existingJobUndone],this.callback);
            },
            "result must be success": resultIsSuccess,
            "there mustn't be errors": assertNoError,
            "but if adding it again": {
                topic: function(a) {
                    console.log(a);
                    callServer("addTask", [existingProject, existingJobUndone],this.callback);
                },
                "there must be error": assertHasError('DuplicateTask'),
                "ne result must be returned": assertNoResult
            }
        }


    }
//}).export(module);
}).run();
