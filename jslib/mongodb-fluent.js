// functions to make work with MongoDB for nodejs easier.

var mongodb = require('./mongodb');

var ErrorType = 'MongoDBError';

/*var Client = function(server) {
    this.server = server;
    this.nativeParser = true;
}*/


var onMongodbError = function(err, client, onError){
    if (onError) {
        process.nextTick(onError.bind({},{type: ErrorType, msg: err.message}));
    }
    client.close();
    console.log("mongo error");
    console.log(err);
    console.log("mongo error end");
};


var getDbClient = function(server, dbName) {
    return new mongodb.Db(dbName, server, {native_parser: true});
};

// Finds documents in database and provides cursor to callback as an arguments
// onFinished: function(cursor)
// onError: function(errorObject)
var find = function(client, collectionName, spec, fields, onFinished, onError) {
    //var client = this.getDbClient(db);
    
    var onHasConnection = function() {
        client.collection(collectionName, function(err, collection) {
            if (err) { onMongodbError(err, client, onError); return; }
            collection.find(spec, fields, function(err, cursor){
                if (err) { onMongodbError(err, client, onError); return; }
                if (onFinished)
                    process.nextTick( onFinished.bind({}, cursor) );
            });
        } );
    };
    
    if (client.state == 'connected') {
        onHasConnection();
    } else {
        client.open(function(err, pClient) {
            if (err) { onMongodbError(err, client, onError); return; }
            onHasConnection();
        });
    }
};


var findOne = function(client, collectionName, spec, fields, onFinished, onError) {
    client.open(function(err, pClient) {
        if (err) { onMongodbError(err, client, onError); return; }
        client.collection(collectionName, function(err, collection) {
            if (err) { onMongodbError(err, client, onError); return; }
            var opts = {limit: 1};
            collection.find(spec, fields, opts, function(err, cursor){
                if (err) { onMongodbError(err, client, onError); return; }
                cursor.nextObject(function(err, obj){
                    if (err) { onMongodbError(err, client, onError); return; }
                    if (onFinished)
                        process.nextTick( onFinished.bind({}, obj) );
                });
            });
        } );
    });
};

// Update documents in database.
// onFinished: function()
// onError: function(errorObject)
var update = function(client, collectionName, spec, changes, options, onFinished, onError) {
    // var client = this.getDbClient(db);
    client.open(function(err, pClient) {
        if (err) { onMongodbError(err, client, onError); return; }
        client.collection(collectionName, function(err, collection) {
            if (err) { onMongodbError(err, client, onError); return; }
            collection.update(spec, changes, options, function(err, cursor){
                if (err) {  onMongodbError(err, client, onError); return; }
                if (onFinished) process.nextTick(onFinished);
            });
        } );
    });
};

exports.find = find;
exports.findOne = findOne;
exports.update = update;
