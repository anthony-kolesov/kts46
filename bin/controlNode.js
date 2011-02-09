// Modules
var http = require('http'),
    urllib = require('url'),
    RPCHandler = require('jsonrpc').RPCHandler,
    scheduler = require('../jslib/schedulerRpcWrapper');

// Configuration
var cfg = require('config')('ControlNode', {
  port: 46212,
  address: "",
  jsonRpcPath: "/jsonrpc",
  debugRpc: true
});

// Local variables
var version = "0.1.4"
    versionString = "ControlNode " + version + " on node.js";

var schedulerWrapper = new scheduler.Wrapper(cfg.mongodbAddress);
    
var handleHttpRequest = function(req, res) {
    if(req.method == "POST"){
        // Define whether this is JSON request.
        if (urllib.parse(req.url).pathname == cfg.jsonRpcPath) {
            new RPCHandler(req, res, schedulerWrapper, cfg.debugRpc);
        } else {
            res.writeHead(404, {'Content-Type': 'text/plain'});
            res.end('Unknown path!\n');
        }
    } else {
        res.writeHead(200, {'Content-Type': 'text/plain'});
        //res.end('Hello World\n');
        res.end(JSON.stringify(schedulerWrapper.getStatus(), null, 4))
    }
};


// Run server.
http.createServer(handleHttpRequest).listen(cfg.port, cfg.address);
console.log(['Server running at http://', cfg.address, ':', cfg.port, ' on ',
             process.version].join(''));
