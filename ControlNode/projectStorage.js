var mongodb = require('mongodb'),
    fluentMongodb = require('./mongodb-fluent');

function Storage(dbServer) {
    this.dbServer = dbServer;
    this.infoDbName = "kts46_info";
    this.infoDb = null;
};

Storage.prototype._getDbClient = function(projectName) {
    return new mongodb.Db(projectName, this.dbServer, {native_parser: true});
};

/*
Callbacks:
    onHasJob(job)
    onError(error)
*/
Storage.prototype.getJob = function(projectName, jobName, onHasJob, onError) {
    var onJobLoaded = function(client1, jobDocument) {
        if (jobDocument === null) {
            if (onHasJob) onHasJob(null);
            return;
        }

        var j = {
            duration: jobDocument.definition.simulationParameters.duration,
            batchLength: jobDocument.definition.simulationParameters.batchLength,
            stepDuration: jobDocument.definition.simulationParameters.stepDuration,
            name: jobDocument.name,
            id: jobDocument._id
        };
        fluentMongodb.findOne(client1, 'progresses', {'_id': j.id}, {},
            onProgressLoaded.bind({}, client1, j), onError );
    };

    var onProgressLoaded = function(client2, job, progressDocument) {
        job.fullStatistics = progressDocument.fullStatistics;
        job.done = progressDocument.done;
        job.totalSteps = progressDocument.totalSteps;
        job.batches = progressDocument.batches;
        // job.jobname = progressDocument.jobname;
        job.basicStatistics = progressDocument.basicStatistics;
        job.idleTimes = progressDocument.idleTimes;
        job.throughput = progressDocument.throughput;

        client2.close();
        process.nextTick( onHasJob.bind({}, job) );
    };

    var spec = {'_id': jobName};
    var fields = {'name':1, 'definition': 1};
    var client = this._getDbClient(projectName);
    fluentMongodb.findOne(client, 'jobs', spec, fields,
                          onJobLoaded.bind({}, client), onError);
};


Storage.prototype.saveStatistics = function(statistics, onFinished, onError) {
    if (this.infoDb === null) {
        this.client = this._getDbClient(this.infoDbName);
    }
    var onDone = function() {
        if (onFinished)
            process.nextTick( onFinished );
    };
    fluentMongodb.insert(this.infoDb, "workerStatistics", statistics, {}, onDone, onError);
};


/**
 * Gets names of projects in database.
 *
 * @param onFinished {function(Array<String>)}
 * @param onError {function(Error)}
*/
Storage.prototype.getProjectsNames = function(onFinished, onError) {
    //if (this.infoDb === null) {
        this.infoDb = this._getDbClient(this.infoDbName);
    //}
    var onLoaded = function(cursor){
        cursor.toArray(function(err, data){
            if (onFinished) {
                onFinished(data.map(function(it){ return it['_id']; }));
            }
            cursor.close();
        });
    };
    fluentMongodb.find(this.infoDb, "projects", {}, {'_id':1},onLoaded, onError);
};


/**
 * Gets jobs status.
 *
 * @param onReady {function(Array<Job>)}
 * @param onError {function(Error)}
 */
Storage.prototype.getStatus = function(onReady, onError){
    var self = this;
    var onHasNames = function(projectsNames){
        var fields = {name:1, done:1, totalSteps:1, basicStatistics:1,
            idleTimes:1, fullStatistics:1, throughput:1};
        var progresses = [];
        var getForProject = function() {
            if (projectsNames.length > 0) {
                var name = projectsNames.shift();
                var client = self._getDbClient(name);
                fluentMongodb.find(client, "progresses", {}, fields, function(cursor){
                    cursor.toArray(function(err, array){
                        for (var i in array) {
                            array[i].name = array[i].name || array[i]['_id'];
                            array[i].project = name;
                            progresses.push(array[i]);
                        }
                        getForProject();
                        //cursor.close(); // Causes error on second request.
                        client.close();
                    });
                }, onError);
            } else {
                if (onReady) {
                    process.nextTick(function(){onReady(progresses);});
                }
            }
        };
        getForProject();
    };
    this.getProjectsNames(onHasNames, onError);
};


Storage.prototype.getJobStatistics = function(projectName, jobName, onDone, onError){
    var fields = {name:1, done:1, totalSteps:1, basicStatistics:1,
        idleTimes:1, fullStatistics:1, throughput:1};
    var client = this._getDbClient(projectName);
    fluentMongodb.findOne(client, "progresses", {"_id":jobName}, fields, function(doc){
        if (doc !== null) {
            doc.name = doc.name || doc['_id'];
            doc.project = projectName;
        }
        client.close();
        if (onDone) {
            process.nextTick(onDone.bind({}, doc));
        }

    }, onError);
};

Storage.prototype.getModelDefinition = function(projectName, jobName, onDone, onError){
    var fields = {definition:1};
    var client = this._getDbClient(projectName);
    fluentMongodb.findOne(client, "jobs", {"_id":jobName}, fields, function(doc){
        if (onDone) {
            process.nextTick(onDone.bind({}, doc!==null?doc.definition:null) );
        }

    }, onError);
};

Storage.prototype.getModelState = function(projectName, jobName, time, onDone, onError){
    var fields = {definition:1};
    var client = this._getDbClient(projectName);
    fluentMongodb.findOne(client, "states", {"_id":jobName}, fields, function(doc){
        if (onDone) {
            if (doc === null)
                process.nextTick(onDone.bind({}, null) );
            else {
                process.nextTick(onDone.bind({}, doc!==null?doc.definition:null) );
            }
        }
    }, onError);
};


exports.Storage = Storage;
