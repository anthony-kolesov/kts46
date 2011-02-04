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
var assertArgTypeInvalid = function(){
    return function(r, e) {
        return assertHasError("InvalidArgumentType");
    };
};
var assertHasError = function(errorName){
    return function(r, e) {
        assert.isNotNull(r.error);
        assert.strictEqual(r.error.type, errorName);
    };
};
var assertNoResult = function() {
    return function(r, e) {
        assert.isNull(r.result);
    }
};
var assertErrorArgName = function(argName) {
    return function(r, e) {
        assert.isNotNull(r.error);
        assert.strictEqual(r.error.argumentName, argName);
    };
};

var resultIsSuccess = function() {
    return function(r, e) {
        assert.strictEqual(r.result, "success");
    };
};
var assertNoError = function() {
    return function(r, e) {
        assert.isNull(r.error);
        assert.isNotNull(r.result);
    }
};

vows.describe('kts46 Control node scheduler').addBatch({

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
            "InvalidTypeArgument must be raised": assertArgTypeInvalid(),
            "result must be null": assertNoResult(),
            "argument name must be projectName": assertErrorArgName("projectName")
        },
        "with null project name": {
            topic: function(){callServer("addTask", [null, "j1"],this.callback);},
            "InvalidTypeArgument must be raised": assertArgTypeInvalid(),
            "result must be null": assertNoResult(),
            "argument name must be projectName": assertErrorArgName("projectName")
        },
        "with invalid job name": {
            topic: function(){callServer("addTask", ["p1", 1], this.callback);},
            "InvalidTypeArgument must be raised": assertArgTypeInvalid(),
            "result must be null": assertNoResult(),
            "argument name must be jobName": assertErrorArgName("jobName")
        },
        "with null job name": {
            topic: function(){callServer("addTask", ["p1", null], this.callback);},
            "InvalidTypeArgument must be raised": assertArgTypeInvalid(),
            "result must be null": assertNoResult(),
            "argument name must be jobName": assertErrorArgName("jobName")
        },

        "for project that doesn't exist": {
            topic: function() {
                callServer("addTask", [unexistingProject, existingJob], this.callback);
            },
            "there mustn't be result": assertNoResult(),
            "there must be JobNotFound": assertHasError("JobNotFound")
        },

        "for job that doesn't exist": {
            topic: function() {
                callServer("addTask", [existingProject, unexistingJob], this.callback);
            },
            "there mustn't be result": assertNoResult(),
            "there must be JobNotFound": assertHasError("JobNotFound")
        },

        "with valid args for done task": {
            topic: function() {
                callServer("addTask", [existingProject, existingJobDone],
                           this.callback);
            },
            "there mustn't be result": assertNoResult(),
            "there must be AlreadyDone": assertHasError("AlreadyDone")
        },

        "for undone task": {
            topic: function() {
                callServer("addTask", [existingProject, existingJobUndone],this.callback);
            },
            "result must be success": resultIsSuccess(),
            "there mustn't be errors": assertNoError()
        }
    },

    "when calling abortTask": {
        "with invalid project name type": {
            topic: function(){callServer("abortTask", [1234, existingJobUndone], this.callback);},
            "InvalidTypeArgument must be raised": assertArgTypeInvalid(),
            "result must be null": assertNoResult(),
            "argument name in error must be projectName":
                assertErrorArgName("projectName")
        },
        "with invalid job name": {
            topic: function(){callServer("abortTask", [existingProject, 1], this.callback);},
            "InvalidTypeArgument must be raised": assertArgTypeInvalid(),
            "result must be null": assertNoResult(),
            "argument name must be jobName": assertErrorArgName("jobName")
        }
    },

    "when calling getTask": {
        "with invalid workerId type": {
            topic: function(){callServer("getTask", [1234, ['simulation']],
                                         this.callback);},
            "InvalidTypeArgument must be raised": assertArgTypeInvalid(),
            "result must be null": assertNoResult(),
            "argument name in error must be correct":
                assertErrorArgName("workerId")
        },
        "with invalid type of taskTypes": {
            topic: function(){callServer("getTask", ["lala", "simulation"],
                                         this.callback);},
            "InvalidTypeArgument must be raised": assertArgTypeInvalid(),
            "result must be null": assertNoResult(),
            "argument name must be correct": assertErrorArgName("taskTypes")
        },
        "with invalid type in the taskTypes": {
            topic: function(){callServer("getTask",
                                         ["lala", ["simulation", 1, "basicStatistics"]],
                                         this.callback);},
            "InvalidTypeArgument must be raised": assertArgTypeInvalid(),
            "result must be null": assertNoResult(),
            "argument name must be correct": assertErrorArgName("taskTypes[1]")
        },
        "with invalid name of task type": {
            topic: function(){callServer("getTask",
                                         ["lala", ["simulation", "trololololo"]],
                                         this.callback);},
            "InvalidTypeArgument must be raised": assertHasError("UnknownTaskType"),
            "result must be null": assertNoResult(),
            "argument name must be correct": assertErrorArgName("taskTypes[1]")
        },
        "with empty list of task types": {
            topic: function(){callServer("getTask", ["lala", []], this.callback);},
            "all must be ok": assertNoError(),
            "nothing must be returned": function(r, e){
                assert.isTrue(r.result.empty);
            }
        },
        "with empty list (with null) of task types": {
            topic: function(){callServer("getTask", ["lala", [null]], this.callback);},
            "all must be ok": assertNoError(),
            "nothing must be returned": function(r, e){
                assert.isTrue(r.result.empty);
            }
        },
        "with task that is unavailable": {
            topic: function(){callServer("getTask", ["lala", ["idleTimes"]], this.callback);},
            "all must be ok": assertNoError(),
            "nothing must be returned": function(r, e){
                assert.isTrue(r.result.empty);
            }
        }
    },

    "when calling acceptTask": {
        "with invalid workerId type": {
            topic: function(){callServer("acceptTask", [1234, "sig"], this.callback);},
            "InvalidTypeArgument must be raised": assertArgTypeInvalid(),
            "result must be null": assertNoResult(),
            "argument name in error must be correct": assertErrorArgName("workerId")
        },
        "with invalid sig type": {
            topic: function(){callServer("acceptTask", ["lalala", 1], this.callback);},
            "InvalidTypeArgument must be raised": assertArgTypeInvalid(),
            "result must be null": assertNoResult(),
            "argument name in error must be correct": assertErrorArgName("sig")
        }
    },

    "when calling rejectTask": {
        "with invalid workerId type": {
            topic: function(){callServer("rejectTask", [1234, "sig"], this.callback);},
            "InvalidTypeArgument must be raised": assertArgTypeInvalid(),
            "result must be null": assertNoResult(),
            "argument name in error must be correct": assertErrorArgName("workerId")
        },
        "with invalid sig type": {
            topic: function(){callServer("rejectTask", ["lalala", 1], this.callback);},
            "InvalidTypeArgument must be raised": assertArgTypeInvalid(),
            "result must be null": assertNoResult(),
            "argument name in error must be correct": assertErrorArgName("sig")
        }
    },

    "when calling taskInProgress": {
        "with invalid workerId type": {
            topic: function(){callServer("taskInProgress", [1234, "sig"], this.callback);},
            "InvalidTypeArgument must be raised": assertArgTypeInvalid(),
            "result must be null": assertNoResult(),
            "argument name in error must be correct": assertErrorArgName("workerId")
        },
        "with invalid sig type": {
            topic: function(){callServer("taskInProgress", ["lalala", 1], this.callback);},
            "InvalidTypeArgument must be raised": assertArgTypeInvalid(),
            "result must be null": assertNoResult(),
            "argument name in error must be correct": assertErrorArgName("sig")
        }
    },

    "when calling taskFinished": {
        "with invalid workerId type": {
            topic: function(){callServer("taskFinished", [1234, "sig"], this.callback);},
            "InvalidTypeArgument must be raised": assertArgTypeInvalid(),
            "result must be null": assertNoResult(),
            "argument name in error must be correct": assertErrorArgName("workerId")
        },
        "with invalid sig type": {
            topic: function(){callServer("taskFinished", ["lalala", 1], this.callback);},
            "InvalidTypeArgument must be raised": assertArgTypeInvalid(),
            "result must be null": assertNoResult(),
            "argument name in error must be correct": assertErrorArgName("sig")
        }
    },

    "when calling getCurrentTasks": {
        topic: function(){callServer("getCurrentTasks", [], this.callback);},
        "there mustn't an error": assertNoError()
    },

    "when calling restartTasks": {
        topic: function(){callServer("restartTasks", [[{'id':'aa','sig':'bb'}]], this.callback);},
        "there mustn't an error": assertNoError(),
        "result mut be zero": function(r, e) {
            assert.strictEqual(r.result.restarted, 0);
        }
    }

}).export(module);
//}).run();
