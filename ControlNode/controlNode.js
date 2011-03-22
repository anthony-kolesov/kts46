// Modules
var http = require('http'),
    urllib = require('url'),
    RPCHandler = require('jsonrpc').RPCHandler,
    scheduler = require('./schedulerRpcWrapper'),
    handleStaticFile = require('./staticFileHandler').handle,
    fs = require('fs'),
    ProjectStorage = require('./projectStorage').Storage,
    dataApi = require("./data_api"),
    mongodb = require('mongodb'),
    getDataHandler = require("./GetDataHandler");

// Configuration
var cfg = require('config')('ControlNode', {
  port: 46400,
  address: "",
  jsonRpcPath: "/jsonrpc",
  debugRpc: false,
  statusPath: "/status",
  webuiFilesPath: "../http_server/web",
  webuiPathRoot: "/ui",

  dbHost: '192.168.42.3',
  dbPort: 27017
});

// Local variables
var version = "0.1.6",
    versionString = ["ControlNode=", version, ";NodeJS=", process.version].join(""),
    logfile = fs.createWriteStream("/var/log/kts46/ControlNode.log", {flags:"a"});


var log = function(msg){
    logfile.write([Date(), msg + "\n"].join("\t"));
};
var logRequest = function(code, path){
    logfile.write([Date(), code, path + "\n"].join("\t"));
};



var projectStorage = new ProjectStorage(new mongodb.Server(cfg.dbHost, cfg.dbPort, {}));
var schedulerWrapper = new scheduler.Wrapper();

var handleHttpRequest = function(req, res) {
    var url = urllib.parse(req.url, true),
        path = url.pathname,
        query = url.query;
    if(req.method == "POST"){
        // Define whether this is JSON request.
        if (path == cfg.jsonRpcPath) {
            logRequest(200, path);
            new RPCHandler(req, res, schedulerWrapper, cfg.debugRpc);
        } else {
            logRequest(404, path);
            res.writeHead(404, {'Content-Type': 'text/plain'});
            res.end('Unknown path!\n');
        }
    } else if (path === cfg.statusPath) {
        logRequest(200, path);
        res.writeHead(200, {'Content-Type': 'application/json'});
        res.end(JSON.stringify(schedulerWrapper.getStatus(), null, 4))
    } else if (path === "/api/data") {
        logRequest(200, path);
        //res.writeHead(200, {'Content-Type': 'application/json'});
        //dataApi.serverStatus(projectStorage, query, res);
        var dataMethods = {
            serverStatus: dataApi.serverStatus.bind({}, projectStorage),
            getJobStatistics: dataApi.getJobStatistics.bind({}, projectStorage),
            getModelDefinition: dataApi.getModelDefinition.bind({}, projectStorage)
        };
        getDataHandler.handle(query, res, dataMethods);
    } else {
        logRequest(200, path);
        handleStaticFile(cfg.webuiFilesPath, cfg.webuiPathRoot, req, res);
    }
};


// Run server.
http.createServer(handleHttpRequest).listen(cfg.port, cfg.address);
var startingMsg = ["Starting ", versionString, " at http://", cfg.address, ':', cfg.port].join('');
console.log(startingMsg);
logfile.write([Date(), "\t", startingMsg, "\n"].join(""))
