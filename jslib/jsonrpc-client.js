/* Copyright 2010-2011 Anthony Kolesov

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

var http = require('http');


/**
  JSON-RPC web client.

  Arguments:
    host {string} JSON-RPC server host.
    @param port {int} port on the host (default: 80).
    path - HTTP request path (default: /jsonrpc).
*/
function JSONRPC_Client(host, port, path) {
    this.options = {
        'host': host,
        'port': port || 80,
        'path': path || '/jsonrpc',
        'method': 'POST'
    };
    this.requestId = 0;
}

JSONRPC_Client.prototype.call = function() {
    var methodName = arguments.shift();
    var callback = arguments.pop();
    var params = [];
    for (var i=0, l=arguments.length; i < l; ++i){
        params.push(arguments[i]);
    }
    var callObject = {"method": method, "params":params, "id": this.requestId++};

    var onResponse = function(callback, dataChunk) {
        callback(JSON.parse(dataChunk));
    }

    var request = http.request(this.options, function(response) {
        response.setEncoding('utf8');
        response.on('data', onResponse.bind({}, callback));
    });

    // write data to request body
    request.write(JSON.stringify(callObject));
    request.end();
};

exports.Client = JSONRPC_Client;
