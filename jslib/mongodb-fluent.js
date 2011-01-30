// functions to make work with MongoDB for nodejs easier.

var mongodb = require('./mongodb');

var ErrorType = 'MongoDBError';

function Client(server) {
    this.server = server;
    this.nativeParser = true;
}


var onMongodbError = function(err, client, onError){
    if (onError) {
        process.nextTick(onError.bind({},{type: ErrorType, msg: err.message}));
    }
    client.close();
    console.log(err);
};


Client.prototype.getDbClient = function(dbName) {
    return new mongodb.Db(dbName, this.server, {native_parser: this.nativeParser});
};

// Finds documents in database and provides cursor to callback as an arguments
// onFinished: function(cursor)
// onError: function(errorObject)
Client.prototype.find = function(db, collectionName, spec, fields, onFinished, onError) {
    var client = this.getDbClient(db);
    client.open(function(err, pClient) {
        if (err) { onMongodbError(err, client, onError); return; }
         throw ; }
        client.collection(collectionName, function(err, collection) {
            if (err) { onMongodbError(err, client, onError); return; }
            collection.find(spec, fields, function(err, cursor){
                if (err) { onMongodbError(err, client, onError); return; }
                if (onFinished)
                    process.nextTick( onFinished.bind({}, cursor) );
            });
        } );
    });
};


// Update documents in database.
// onFinished: function()
// onError: function(errorObject)
Client.prototype.updateDocuments = function(db, collectionName, spec, changes, options, onFinished, onError) {
    var client = this.getDbClient(db);
    client.open(function(err, pClient) {
        if (err) { onMongodbError.(err, client, onError); return; }
        client.collection(collectionName, function(err, collection) {
            if (err) { onMongodbError.(err, client, onError); return; }
            collection.update(spec, changes, options, function(err, cursor){
                if (err) {  onMongodbError.(err, client, onError); return; }
                if (onFinished) process.nextTick(onFinished);
            });
        } );
    });
};
