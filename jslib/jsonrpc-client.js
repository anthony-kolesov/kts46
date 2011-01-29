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
    this.requestId = 1; // Don't start with error or call will not work.
}


JSONRPC_Client.prototype.call = function(methodName) {
    var cbk = arguments[arguments.length-1];
    var params = [];
    for (var i=1, l=arguments.length-2; i < l; ++i)
        params.push(arguments[i]);

    var callObject = {method: methodName, params:params, id: this.requestId++};

    var onResponse = function (callback, chunk) {
        callback(JSON.parse(chunk));
    };

    var req = http.request(this.options, function(res) {
        res.setEncoding('utf8');
        res.on('data', onResponse.bind({}, cbk));
    });
    // write data to request body
    req.write(JSON.stringify(callObject));
    req.end();
};

exports.Client = JSONRPC_Client;
