var mongodb = require('./mongodb'),
    fluentMongodb = require('./mongodb-fluent');

var Storage = function(dbServer) {
    this.dbServer = dbServer;
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
    var onJobLoaded = function(jobDocument) {
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
        fluentMongodb.findOne(client, 'progresses', {}, {},
            onProgressLoaded.bind({}, j), onError );
    };
    
    var onProgressLoaded = function(job, progressDocument) {
        job.fullStatistics = progressDocument.fullStatistics;
        job.done = progressDocument.done;
        job.totalSteps = progressDocument.totalSteps;
        job.batches = progressDocument.batches;
        // job.jobname = progressDocument.jobname;
        job.basicStatistics = progressDocument.basicStatistics;
        job.idleTimes = progressDocument.idleTimes;
        job.throughput = progressDocument.throughput;
        
        client.close();
        process.nextTick( onHasJob.bind({}, job) );
    };
    
    var spec = {'_id': jobName};
    var fields = {'name':1, 'definition': 1};
    var client = this._getDbClient(projectName);
    fluentMongodb.findOne(client, 'jobs', spec, fields, onJobLoaded, onError);
};

exports.Storage = Storage;
