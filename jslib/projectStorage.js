var mongodb = require('./mongodb'),
    fluentMongodb = require('./mongodb-fluent');

var Storage = function(dbServer) {
    this.projects = {};
    this.dbServer = dbServer;
};


var Project = function(name){
    this.name = name;
    this.jobs = {};
};

Project.prototype.hasJob = function(jobName){
    return this.jobs.hasOwnProperty(jobName);
};

Project.prototype.getJob = function(jobName){
    return this.jobs[jobName];
};

Project.prototype.addJob = function(jobInfo){
    this.jobs[jobInfo.jobname] = jobInfo;
};


Storage.prototype._getDbClient = function(projectName) {
    return new mongodb.Db(projectName, this.dbServer, {native_parser: true});
};


// onFinished: function()
// onError: function(ErrorObject)
Storage.prototype._loadProject = function(project, onFinished, onError) {

    var onJobInfoLoaded = function(client, cursor) {
        cursor.toArray(function(err, a){
            a.forEach(function(item, index, array){
                var j = project.getJob(item.name);
                j.duration = item.simulationParameters.duration;
                j.batchLength = item.simulationParameters.batchLength;
                j.stepDuration = item.simulationParameters.stepDuration;
                // Last
                if (index === array.length - 1) {
                    cursor.close();
                    client.close();
                    if (onFinished) process.nextTick(onFinished);
                }
            });
        }
    };

    var loadJobInfo = (function() {
        var client = this._getDbClient(project.name);
        fluentMongodb.find(client, 'jobs', {}, {'yaml':0},
            onJobInfoLoaded.bind(this,client), onError );
    }).bind(this);

    var onProgressesLoaded = function(cursor) {
        cursor.toArray(function(err, a){
            a.forEach(function(item, index, array){
                var j = {
                    '_id': item._id,
                    'fullStatistics': item.fullStatistics,
                    'done': item.done,
                    'totalSteps': item.totalSteps,
                    'batches': item.batches,
                    'jobname': item.jobname,
                    'basicStatistics': item.basicStatistics,
                    'idleTimes': item.idleTimes,
                    'throughput': item.throughput
                };
                project.addJob(j);
                if (index === array.length - 1) {
                    cursor.close();
                    client.close();
                    process.nextTick(loadJobInfo);
                }
            });
        }
    };

    var fields =  {'currentFullState': 0};
    var client = context._getDbClient(project.name);
    fluentMongodb.find(client, 'progresses', {}, fields, onProgressesLoaded, onError);
};

// Checks whether specified project exists.
Storage.prototype.hasProject = function(projectName, onExists, onNotExists, onError) {
    var stor = this;
    if (projects.hasOwnProperty(projectName)) {
        if (onExists) process.nextTick(onExists.bind({}, this.projects[projectName]));
    } else {
        // Try to find it in the database.
        var client = this._getDbClient(projectName);
        fluentMongodb.find(client, 'info', {'_id': 'project'}, {}, function(cursor){ 
            cursor.count(function(err, number){
                cursor.close();
                client.close();
                if (err) {
                    if (onError) process.nextTick(onError.bind(err));
                } else if (number === 0) {
                    if (onNotExists) process.nextTick(onNotExists);
                } else {
                    // Store info in cache.
                    var p = this.projects[projectName] = new Project(projectName);
                    stor._loadProject(p, function(){ if (onExists) onExists(p);});
                } 
            });
        }, onError);
    }
};

// Checks whether specified job exists.
var jobExists = function(projectName, jobName, onExists, onNotExists) {
    var handleProjectExists = function(project) {
        if (project.hasJob(jobName)) {
            if (onExists) onExists(project, project.getJob(jobName));
        } else {
            if (onNotExists) onNotExists();
        }
    };
    projectExists.bind(this)(projectName, handleProjectExists, onNotExists);
};




exports.Storage = Storage;

