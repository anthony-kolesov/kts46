var http = require('http'),
  RPCHandler = require('jsonrpc').RPCHandler,
  address = "127.0.0.1",
  versionString = "ControlNode v0.1.3 on nodejs",
  port = 46212,
  rpcMethods = {
    hello: function(rpc){
      rpc.response("Hello! I am " + versionString);
    }
  }
;

http.createServer(function (req, res) {
  if(req.method == "POST"){
    // if POST request, handle RPC
    new RPCHandler(req, res, rpcMethods, false);
  } else {
    res.writeHead(200, {'Content-Type': 'text/plain'});
    res.end('Hello World\n');
  }
}).listen(port, address);

console.log(['Server running at http://', address, ':', port, '/'].join(''));
