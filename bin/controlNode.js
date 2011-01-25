// Modules
var http = require('http'),
    urllib = require('url'),
    RPCHandler = require('jsonrpc').RPCHandler,
    scheduler = require('./kts46-scheduler');


// Configuration
var cfg = {
  port: 46212,
  address: "",
  jsonRpcPath: "/jsonrpc",
  debugRpc: false
};


// Local variables
var version = "0.1.4"
    versionString = "ControlNode " + version + " on node.js";

var handleHttpRequest = function(req, res) {
  if(req.method == "POST"){
    // Define whether this is JSON request.
    if (urllib.parse(req.url).pathname == cfg.jsonRpcPath) {
      new RPCHandler(req, res, scheduler.rpcMethods, cfg.debugRpc);
    } else {
      res.writeHead(404, {'Content-Type': 'text/plain'});
      res.end('Unknown path!\n');
    }
  } else {
    res.writeHead(200, {'Content-Type': 'text/plain'});
    res.end('Hello World\n');
  }
};


// Run server.
http.createServer(handleHttpRequest).listen(cfg.port, cfg.address);
console.log(['Server running at http://', cfg.address, ':', cfg.port, '/'].join(''));
