var RPCClient = require('../jslib/jsonrpc-client').Client,
    callServer = require('../jslib/jsonrpc-client').callServer,
    assert = require('assert');

// Setup assert.
//as.isString = function(value, msg) {
//    as.ok(value instanceof String, msg)
//};


var getClient = function() {
    return new RPCClient('192.168.1.2', 46212);
}
var client = getClient();


var onHello = function(data) {
    console.log('aa');
    assert.ok(data instanceof Number, "sdasdasd");
};


client.call('hello', [], onHello);
// callServer('hello', [], onHello);
