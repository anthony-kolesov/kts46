// Modules
var http = require('http'),
    urllib = require('url'),
    RPCHandler = require('jsonrpc').RPCHandler,
    scheduler = require('./schedulerRpcWrapper'),
    handleStaticFile = require('./staticFileHandler').handle,
    fs = require('fs');

// Configuration
var cfg = require('config')('ControlNode', {
  port: 46212,
  address: "",
  jsonRpcPath: "/jsonrpc",
  debugRpc: false,
  statusPath: "/status",
  webuiFilesPath: "../http_server/web",
  webuiPathRoot: ""
});

// Local variables
var version = "0.1.6",
    versionString = ["ControlNode=", version, ";NodeJS=", process.version].join(""),
    logfile = fs.createWriteStream("/var/log/kts46/ControlNode.log", {flags:"a"});

var log = function(code, path){
    logfile.write([Date(), code, path + "\n"].join("\t"));
};


var schedulerWrapper = new scheduler.Wrapper(cfg.mongodbAddress);

var handleHttpRequest = function(req, res) {
    var path = urllib.parse(req.url).pathname;
    if(req.method == "POST"){
        // Define whether this is JSON request.
        if (path == cfg.jsonRpcPath) {
            log(200, path);
            new RPCHandler(req, res, schedulerWrapper, cfg.debugRpc);
        } else {
            log(404, path);
            res.writeHead(404, {'Content-Type': 'text/plain'});
            res.end('Unknown path!\n');
        }
    } else if (path === cfg.statusPath) {
        log(200, path);
        res.writeHead(200, {'Content-Type': 'application/json'});
        res.end(JSON.stringify(schedulerWrapper.getStatus(), null, 4))
    } else {
        log(200, path);
        handleStaticFile(cfg.webuiFilesPath, cfg.webuiPathRoot, req, res);
    }
};


// Run server.
http.createServer(handleHttpRequest).listen(cfg.port, cfg.address);
var startingMsg = ["Starting ", versionString, " at http://", cfg.address, ':', cfg.port].join('');
console.log(startingMsg);
logfile.write([Date(), "\t", startingMsg, "\n"].join(""))
