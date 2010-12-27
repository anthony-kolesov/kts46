"""
License:
   Copyright 2010 Anthony Kolesov

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import logging, BaseHTTPServer, re, xmlrpclib, json


class JSONApiServer:
    "Provides HTTP server that provides control over simulation with JSON API."

    def __init__(self, cfg):
        self.server = self.createProxy(cfg)
        self.cfg = cfg

    def server_forever(self):
        server_address = ('', 46211)
        httpd = BaseHTTPServer.HTTPServer(server_address, JSONApiRequestHandler)
        httpd.rpc_server = self.server
        httpd.serve_forever()

    def createProxy(self, cfg):
        # Create RPC proxy.
        host = cfg.get('json_api', 'server')
        port = cfg.getint('rpc-server', 'port')
        connString = 'http://%s:%i' % (host, port)
        proxy = xmlrpclib.ServerProxy(connString)
        return proxy


class JSONApiRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):
        match = re.match(r"/api/(\w+)/", self.path)
        if match is None:
            self.send_response(404)
            self.end_headers()
            return

        rpc = self.server.rpc_server
        functionName = match.group(1)
        if functionName == 'projectStatus':
            functionMatch = re.match(r"/api/(\w+)/(\w+)/", self.path)
            projectName = functionMatch.group(2)
            data = rpc.getProjectStatus(projectName)
        else:
            data = None

        if data is None:
            self.send_response(404)
            self.end_headers()
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(data))

