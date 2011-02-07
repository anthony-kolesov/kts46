/*
Copyright 2010-2011 Anthony Kolesov

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

var mongodb = require('../jslib/mongodb'),
    fluentMongodb = require('../jslib/mongodb-fluent'),
    ProjectStorage = require('../jslib/projectStorage').Storage;


var onMongodbError = function(response, err){
    response.error({type: 'MongoDBError', msg: err.message});
};


// Scheduler constants
var taskType = { simulation: "simulation", basicStatistics: "basicStatistics",
  idleTimes: "idleTimes", throughput: "throughput",
  fullStatistics: "fullStatistics"
};


var Scheduler = function(){
    this.mongodbAddress = ['192.168.1.5', 27017];
    this.projectStorage = new ProjectStorage(getDbServer(this));
    this.waitingQueue = [];
    this.waitingActivation = {};
    this.runningTasks = {};
};


var getDbServer = function(scheduler) {
    return new mongodb.Server(scheduler.mongodbAddress[0], scheduler.mongodbAddress[1], {});
};


Scheduler.prototype.taskExists = function(projectName, jobName, taskType) {
    var mask = function(task, index) {
        return task.project === projectName && task.job === jobName
                && task.type === taskType;
    };
    if (this.waitingQueue.some(mask)) {
        return true;
    }
    for (var key in this.waitingActivation) {
        if (this.waitingActivation.hasOwnProperty(key)
            && mask(this.waitingActivation[key]) )
            return true;
    }
    for (var key in this.runningTasks) {
        if (this.runningTasks.hasOwnProperty(key)
            && mask(this.runningTasks[key]) )
            return true;
    }
    return false;
};



// Adds required tasks to queue if required.
Scheduler.prototype.addTask = function(response, projectName, jobName, taskTypes) {
    var handleHasJob = function(job){
        if (job === null) {
            response.error({type: 'JobNotFound'});
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
            if (!this.taskExists(projectName, jobName, taskType.simulation)) {
                this.waitingQueue.push(getTask(taskType.simulation));
            } else {
                response.error({type: 'DuplicateTask',
                                taskType:taskType.simulation});
            }
        } else if (job.fullStatistics === false) {
            // Statistics are parallel.
            if (this.taskExists(projectName, jobName, taskType.basicStatistics)) {
                response.error({type: 'DuplicateTask',
                                    taskType:taskType.basicStatistics});
                return;
            }
            if (this.taskExists(projectName, jobName, taskType.idleTimes) ) {
                response.error({type: 'DuplicateTask',
                                    taskType:taskType.idleTimes});
                return;
            }
            if (this.taskExists(projectName, jobName, taskType.throughput) ) {
                response.error({type: 'DuplicateTask',
                                    taskType:taskType.throughput});
                return;
            }

            if (job.basicStatistics === false) {
                this.waitingQueue.push(getTask(taskType.basicStatistics));
            }
            if (job.idleTimes === false) {
                this.waitingQueue.push(getTask(taskType.idleTimes));
            }
            if (job.throughtput === false) {
                this.waitingQueue.push(getTask(taskType.throughput));
            }
        } else {
            response.error({type: 'AlreadyDone'});
            return;
        }
        response.response('success');
    };
    
    this.projectStorage.getJob(projectName, jobName, handleHasJob.bind(this), onMongodbError.bind(response));
};


// Abort task that is in waiting queue or waits activation.
Scheduler.prototype.abortTask = function(response, projectName, jobName) {
    var len = 0,
        queueLen = this.waitingQueue.length;
    // Clear waiting tasks.
    this.waitingQueue = this.waitingQueue.filter(function(item){
        return item.project !== projectName || item.job !== jobName;
    });
    len = queueLen - this.waitingQueue.length;

    // Clear waiting for activation.
    for(var key in this.waitingActivation){
        var val = this.waitingActivation[key];
        if (val.project === projectName && val.job === jobName) {
            delete this.waitingActivation[key];
            len += 1;
        }
    }
    
    // Abort already running.
    for(var key in this.runningTasks){
        var val = this.runningTasks[key];
        if (val.project === projectName && val.job === jobName) {
            delete this.runningTasks[key];
            len += 1;
        }
    }
    
    response.response(len);
};


Scheduler.prototype.getTask = function(response, workerId, taskTypes){
    if (this.waitingActivation.hasOwnProperty(workerId) ||
            this.runningTasks.hasOwnProperty(workerId)) {
        response.error({type: 'WorkerHasTask'});
        return;
    }

    var task = null;
    for(var i=0, l=this.waitingQueue.length; i<l; ++i) {
        var it = this.waitingQueue[i];
        if (taskTypes.indexOf(it.type) !== -1) {
            task = it;
            this.waitingQueue.splice(i, 1);
        }
    }
    
    if (task === null){
        task = {empty: true};
    } else {
        task['empty'] = false;
        task['databases'] = [{host: this.mongodbAddress[0],
                              port: this.mongodbAddress[1]}];
        task['lastUpdate'] = new Date();
        task['sig'] = task['lastUpdate'].toJSON();
        this.waitingActivation[workerId] = task;
    }
    response.response(task);
};


Scheduler.prototype.acceptTask = function(response, workerId, sig){
    if (workerId in this.waitingActivation) {
        var t = this.waitingActivation[workerId];
        if (t.sig === sig) {
            delete this.waitingActivation[workerId];
            this.runningTasks[workerId] = t;
            t.lastUpdate = new Date();
            t.sig = t.lastUpdate.toJSON();
            response.response({sig: t.sig});
        } else {
            response.error({type:'InvalidSignature'});
        }
    } else {
        response.error({type:'InvalidWorkerId'});
    }
};


Scheduler.prototype.rejectTask = function(response, workerId, sig) {
    if (workerId in this.waitingActivation) {
        var t = this.waitingActivation[workerId];
        if (t.sig === sig) {
            delete this.waitingActivation[workerId];
            this.waitingQueue.push(t);
            delete t['sig'];
            delete t['empty'];
            response.response("success");
        } else {
            response.error({type:'InvalidSignature'});
        }
    } else {
        response.error({type:'InvalidWorkerId'});
    }
};


Scheduler.prototype.taskFinished = function(response, workerId, sig) {
    // Check task existence.
    if (!(workerId in this.runningTasks)) {
        response.error({type:'InvalidWorkerId'});
        return;
    }

    var task = this.runningTasks[workerId];
    // Check signature
    if (task.sig !== sig) {
        response.error({type:'InvalidSignature'});
        return;
    }

    delete this.runningTasks[workerId];
    var startNext = false;
    if (task.type === taskType.simulation) {
        startNext = true;
    }

    if (startNext)
        process.nextTick(this.addTask.bind(this, response, task.project, task.job));
};


Scheduler.prototype.taskInProgress = function(response, workerId, sig) {
    // Check task existence.
    if (!(workerId in this.runningTasks)) {
        response.error({type:'InvalidWorkerId'});
        return;
    }

    var task = this.runningTasks[workerId];
    // Check signature
    if (task.sig !== sig) {
        response.error({type:'InvalidSignature'});
        return;
    }

    task.lastUpdate = new Date();
    task.sig = task.lastUpdate.toJSON();
    response.response({'sig':task.sig});
};


Scheduler.prototype.getCurrentTasks = function(response) {
    var result = [];
    //for (var i in waitingQueue) {
    //    result.push(waitingQueue[i]);
    //}
    for (var wid in this.waitingActivation) {
        if (this.waitingActivation.hasOwnProperty(wid)) {
            result.push({'id': wid, 'sig': this.waitingActivation[wid].sig});
        }
    }
    for (var wid in this.runningTasks) {
        if (this.runningTasks.hasOwnProperty(wid)) {
            result.push({'id': wid, 'sig': this.runningTasks[wid].sig});
        }
    }
    response.response(result);
};


Scheduler.prototype.restartTasks = function(response, tasks) {
    var restarted = 0,
        runningTasks = this.runningTasks,
        waitingQueue = this.waitingQueue,
        waitingActivation = this.waitingActivation;
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
    response.response({'restarted': restarted});
};


// All exports are in one place.
exports.Scheduler = Scheduler;
exports.taskTypes = taskType;
