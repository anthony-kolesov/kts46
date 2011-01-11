"""
License:
   Copyright 2010-2011 Anthony Kolesov

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

import logging, BaseHTTPServer, re, json, os.path
from socket import error as SocketException
import kts46.utils

JSON_CONTENT_TYPE = 'application/json'

class JSONApiServer:
    "Provides HTTP server that provides control over simulation with JSON API."

    def __init__(self, cfg):
        self.server = kts46.utils.getRPCServerProxy(cfg)
        self.cfg = cfg

    def serve_forever(self):
        server_address = ('', self.cfg.getint('http-api', 'port'))
        httpd = BaseHTTPServer.HTTPServer(server_address, JSONApiRequestHandler)
        httpd.rpc_server = self.server
        httpd.logger = logging.getLogger('HTTPServer')
        httpd.filesDir = self.cfg.get('http-api', 'filesDir')
        httpd.serve_forever()


class JSONApiRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):
        # check for file request.
        fileMatch = re.match(r"/(web/[^\?]*)(\?v=([0-9]\.?)+)?$", self.path)
        if fileMatch is not None:
            path = fileMatch.group(1)
            if path.find("..") != -1:
                self.send_response(400)
                self.end_headers()
                return

            # Convert path to actual path on the disk.
            path = os.path.join(self.server.filesDir, path)

            if not os.path.exists(path):
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)

            # Specific check for cache manifests.
            if path.find("cache-manifest") != -1:
                self.send_header('Content-Type', "text/cache-manifest")
            ext = os.path.splitext(path)[1]
            if ext == '.js':
                self.send_header('Content-Type', "text/javascript")
            elif ext == '.css':
                self.send_header('Content-Type', "text/css")
            self.end_headers()

            f = open(path)
            lines = f.readlines()
            f.close()
            self.wfile.writelines(lines)
            return

        match = re.match(r"/api/(\w+)/", self.path)
        if match is None:
            self.send_response(404)
            self.end_headers()
            return

        try:
            rpc = self.server.rpc_server
            functionName = match.group(1)
            if functionName == 'projectStatus':
                functionMatch = re.match(r"/api/(\w+)/(\w+)/", self.path)
                projectName = functionMatch.group(2)
                data = rpc.getProjectStatus(projectName)
            elif functionName == 'serverStatus':
                data = rpc.getServerStatus()
            else:
                data = None
        except SocketException, msg:
            self.log_error('Error connecting with RPC-server: %s', msg)
            data = {'result': 'fail',
                    'error': "Couldn't connect to RPC server." }

        if data is None:
            self.send_response(404)
            self.end_headers()
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(data))

    def do_POST(self):
        self.log_message('POST request')

        if self.path.startswith("/json-rpc/"):
            self.handleCall()
            return

        match = re.match(r"/api/(\w+)/", self.path)
        functionName = match.group(1)

        success = True
        found = True

        try:
            if functionName == 'addJob':
                rpc = self.server.rpc_server
                data = json.loads(self.rfile.readline())
                rpc.addJob(data['project'], data['job'], data['definition'])
            elif functionName == 'deleteJob':
                data = json.loads(self.rfile.readline())
                self.server.rpc_server.deleteJob(data['project'], data['job'])
            elif functionName == 'runJob':
                data = json.loads(self.rfile.readline())
                self.server.rpc_server.runJob(data['project'], data['job'])
            else:
                success = False
                found = False
        except SocketException, msg:
            self.log_error('Error connecting with RPC-server: %s', msg)
            data = {'result': 'fail',
                    'error': "Couldn't connect to RPC server." }

        if success:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'result':'success'}))
        elif not success and found:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'result':'fail'}))
        else:
            self.send_response(404)
            self.end_headers()

    def sendRPCResponse(self, result, id, error, httpcode=200):
        self.send_response(httpcode)
        self.send_header('Content-Type', JSON_CONTENT_TYPE)
        self.end_headers()
        self.wfile.write(json.dumps({'result':result, 'id':id, 'error': error}))


    def exceptBadRequest(self, msg, id=None):
        self.sendRPCResponse(None, id, msg, 400)

    def checkJSONArgsNumber(self, params, amount):
        if len(params) != amount:
            self.exceptBadRequest("""Provided number of parameters is invalid.
Required number of params: {0}, but has: {1}.""".format(amount, len(params)), id)

    def handleCall(self):
        # JSON RPC request must be in one line o
        request = json.loads(self.rfile.readline())
        
        if "id" not in request:
            self.exceptBadRequest("""`id` field is missing from JSON RPC request body.
It must be `null` if you want to send notification.""")
            
        id = request['id']
            
        if "method" not in request:
            self.exceptBadRequest("`method` field is missing from JSON RPC request body.", id)
        if "params" not in request:
            self.exceptBadRequest("""`params` field is missing from JSON RPC request body.
It must be an empty array if method has no params.""", id)

        methodName = request['method']
        params = request['params']
        
        if not isinstance(params, type( [] )):
            self.exceptBadRequest("`params` fields must be an array.", id)

        xmlrpc = self.server.rpc_server
        result = "success" # Methods can overwrite this variable.
        try:
            if methodName == "addProject":
                self.checkJSONArgsNumber(params, 1)
                xmlrpc.createProject(params[0])
            elif methodName == "deleteProject":
                self.checkJSONArgsNumber(params, 1)
                xmlrpc.deleteProject(params[0])
        except SocketException, msg:
            self.log_error('Error connecting with RPC-server: %s', msg)
            publicMessage = "Couldn't connect to RPC server."
            self.sendRPCResponse(None, id, publicMessage, 500)

        # If we are here than all was a success.
        self.sendRPCResponse(result, id, None)
