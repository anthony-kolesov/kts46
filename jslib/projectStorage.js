var mongodb = require('./mongodb'),
    fluentMongodb = require('./mongodb-fluent');

var Storage = function(dbServer) {
    this.dbServer = dbServer;
};

Storage.prototype._getDbClient = function(projectName) {
    return new mongodb.Db(projectName, this.dbServer, {native_parser: true});
};

Storage.prototype.getJob = function(projectName, jobName, onHasJob, onError) {
    var onJobLoaded = function(jobDocument) {
        var j = {
            duration: jobDocument.simulationParameters.duration,
            batchLength: jobDocument.simulationParameters.batchLength,
            stepDuration: jobDocument.simulationParameters.stepDuration,
            name: jobDocument.name,
            id: jobDocument._id
        };
        loadJobProgress(j);
        fluentMongodb.findOne(client, 'progresses', {}, {},
            onProgressLoaded.bind({}, job), onError );
    };
    
    var onProgressLoaded = function(job, progressDocument) {
        job.fullStatistics = progressDocument.fullStatistics;
        job.done = progressDocument.done;
        job.totalSteps = progressDocument.totalSteps;
        job.batches = progressDocument.batches;
        job.jobname = progressDocument.jobname;
        job.basicStatistics = progressDocument.basicStatistics;
        job.idleTimes = progressDocument.idleTimes;
        job.throughput = progressDocument.throughput;
        
        client.close();
        process.nextTick( onHasJob.bind({}, job) );
    };
    
    var spec = {'_id': jobName};
    var fields = {'name':1,
        'definition.simulationParameters.duration': 1,
        'definition.simulationParameters.batchLength': 1,
        'definition.simulationParameters.stepDuration': 1};
    var client = this._getDbClient(project.name);
    fluentMongodb.findOne(client, 'jobs', spec, fields, onJobLoaded, onError);
};

exports.Storage = Storage;

/*
API:
    class Storage: 
        method getJob(projectName, jobName)
*/
