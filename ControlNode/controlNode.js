// Modules
var http = require('http'),
    urllib = require('url'),
    RPCHandler = require('jsonrpc').RPCHandler,
    scheduler = require('./schedulerRpcWrapper'),
    handleStaticFile = require('./staticFileHandler').handle;

// Configuration
var cfg = require('config')('ControlNode', {
  port: 46212,
  address: "",
  jsonRpcPath: "/jsonrpc",
  debugRpc: false
});

// Local variables
var version = "0.1.6",
    versionString = ["ControlNode=", version, ";NodeJS=", process.version].join("");

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
    } else if (urllib.parse(req.url).pathname === "/status") {
        res.writeHead(200, {'Content-Type': 'application/json'});
        res.end(JSON.stringify(schedulerWrapper.getStatus(), null, 4))
    } else {
        handleStaticFile('../http_server/web', '', req, res);
    }
};


// Run server.
http.createServer(handleHttpRequest).listen(cfg.port, cfg.address);
console.log([versionString, ";at http://", cfg.address, ':', cfg.port].join(''));
