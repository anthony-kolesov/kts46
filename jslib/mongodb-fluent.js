// functions to make work with MongoDB for nodejs easier.

var mongodb = require('./mongodb');

var ErrorType = 'MongoDBError';

/*var Client = function(server) {
    this.server = server;
    this.nativeParser = true;
}*/


var onMongodbError = function(err, client, onError, description){
    if (onError) {
        process.nextTick(onError.bind({},{type: ErrorType, msg: err.message}));
    }
    client.close();
    console.log("*** mongo error ***");
    console.log(err);
    if (description != null) {
        console.log("* Description:");
        console.log(description);
    }
    console.log("*** mongo error end ***");
};


var getDbClient = function(server, dbName) {
    return new mongodb.Db(dbName, server, {native_parser: true});
};

// Finds documents in database and provides cursor to callback as an arguments
// onFinished: function(cursor)
// onError: function(errorObject)
var find = function(client, collectionName, spec, fields, onFinished, onError) {
    var onHasConnection = function() {
        client.collection(collectionName, function(err, collection) {
            if (err) {
                onMongodbError(err, client, onError, "find.onHasConnection.getCollection [#1]");
                return;
            }
            collection.find(spec, fields, function(err, cursor){
                if (err) {
                    onMongodbError(err, client, onError, "find.onHasConnection.collectionFind [#2]");
                    return;
                }
                if (onFinished)
                    process.nextTick( onFinished.bind({}, cursor) );
            });
        } );
    };
    
    if (client.state === 'connected') {
        onHasConnection();
    } else {
        client.open(function(err, pClient) {
            if (err) {
                onMongodbError(err, client, onError, "find.clientOpen [#3]");
            } else {
                onHasConnection();
            }
        });
    }
};


var findOne = function(client, collectionName, spec, fields, onFinished, onError) {
    var onReady = function(cursor){
        cursor.nextObject(function(err, obj){
            if (err) {
                onMongodbError(err, client, onError, "findOne.onReady.nextObject [#4]");
                return;
            }
            cursor.close();
            if (onFinished) {
                process.nextTick( onFinished.bind({}, obj) );
            }
        });
    };
    find(client, collectionName, spec, fields, onReady, onError);
};


// Update documents in database.
// onFinished: function()
// onError: function(errorObject)
var update = function(client, collectionName, spec, changes, options, onFinished, onError) {
    // var client = this.getDbClient(db);
    client.open(function(err, pClient) {
        if (err) {
            onMongodbError(err, client, onError, "update.clientOpen [#5]");
            return;
        }
        client.collection(collectionName, function(err, collection) {
            if (err) {
                onMongodbError(err, client, onError, "update.getCollection [#6]");
                return;
            }
            collection.update(spec, changes, options, function(err, cursor){
                if (err) {
                    onMongodbError(err, client, onError, "update.collectionUpdate [#7]");
                    return;
                }
                if (onFinished) process.nextTick(onFinished);
            });
        } );
    });
};

// Update documents in database.
// onFinished: function()
// onError: function(errorObject)
var insert = function(client, collectionName, docs, options, onFinished, onError) {
    var onHasConnection = function() {
        client.collection(collectionName, function(err, collection) {
            if (err) { onMongodbError(err, client, onError); return; }
            collection.insert(docs, options, function(err, cursor){
                if (err) {  onMongodbError(err, client, onError); return; }
                if (onFinished) process.nextTick(onFinished);
            });
        } );
    };
    
    if (client.state == "connected") {
        onHasConnection();
    } else {
        client.open(function(err, pClient) {
            if (err) { onMongodbError(err, client, onError); return; }
            onHasConnection();
        });
    }
};

exports.find = find;
exports.findOne = findOne;
exports.update = update;
exports.insert = insert;