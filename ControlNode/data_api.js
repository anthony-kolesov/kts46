var mongodb = require("mongodb"),
    fluentMongodb = require("./mongodb-fluent"),
    ProjectStorage = require('./projectStorage').Storage;

/* Callback will get data as an argument.*/
var serverStatus = function(storage, cb){
    storage.getStatus( cb, function(err){console.log(err); process.exit(1); });
};

exports.serverStatus = serverStatus;
