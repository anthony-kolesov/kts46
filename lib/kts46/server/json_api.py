# Copyright 2010-2011 Anthony Kolesov
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import BaseHTTPServer
import json
import logging
import os.path
import re
import urllib
from socket import error as SocketException
import gviz_api
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
        httpd.logger = logging.getLogger('kts46.server.HTTPServer')
        httpd.filesDir = self.cfg.get('http-api', 'filesDir')
        httpd.serve_forever()


class JSONApiRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass

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

        data = None
        try:
            rpc = self.server.rpc_server
            functionName = match.group(1)
            if functionName == 'projectStatus':
                functionMatch = re.match(r"^/api/projectStatus/([-\w]+)/", self.path)
                projectName = functionMatch.group(2)
                data = rpc.getProjectStatus(projectName)
            elif functionName == 'serverStatus':
                data = rpc.getServerStatus()
            elif functionName == 'serverStatus3':
                data = self.getServerStatus3(rpc)
            elif functionName == 'serverStatus2':
                tqxMatch = re.match(r"^/api/serverStatus2/\?tqx=([^\&]*)", self.path)
                self.server.logger.info(self.path)
                tqx = urllib.unquote( tqxMatch.group(1) ) if tqxMatch is not None else ""
                response = self.getServerStatus2(rpc, tqx)
                self.send_response(200)
                self.send_header('Content-Type', JSON_CONTENT_TYPE)
                self.end_headers()
                self.wfile.write(response)
                return
            elif functionName == 'jobStatistics':
                paramsMatch = re.match(r"/api/jobStatistics/([-\w]+)/([-\w]+)/", self.path)
                if paramsMatch is not None:
                    p = paramsMatch.group(1)
                    j = paramsMatch.group(2)
                    data = rpc.getJobStatistics(p,j, False)
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


    def getServerStatus2(self, rpc, tqx):
        #{"project": "new_project_1", "total": 36000.0, "done": 36000, "name": "exp1-s1"}

        # Prepare data.
        data = rpc.getServerStatus()

        schema = {"project":("string", "Project"), "name":("string", "Job"),
                  "totalSteps": ("number", "Total states"),
                  "done": ("number", "Done steps"),
                  "basicStatistics":("boolean", "Basic stats"),
                  "idleTimes":("boolean", "Idle times"),
                  "throughput":("boolean", "Throughput"),
                  "fullStatistics":("boolean", "All stats")}
        table = gviz_api.DataTable(schema)
        table.LoadData(data)
        columnsOrder = ("project", "name", "done", "totalSteps", "basicStatistics",
                        "idleTimes", "throughput", "fullStatistics")
        response = table.ToResponse(columns_order=columnsOrder, tqx=tqx)
        return response


    def getServerStatus3(self, rpc):
        # Prepare data.
        data = rpc.getServerStatus()

        response = { }

        # Schema
        cols = [  ]
        schema = (("project","string", "Project"),
                  ("name", "string", "Job"),
                  ("done", "number", "Done steps"),
                  ("total", "number", "Total states"),
                  ("statisticsFinished", "boolean", "Has stats"))
        for col in schema:
            cols.append({'id': col[0], 'type': col[1], 'label': col[2]})
        response['cols'] = cols

        # Rows
        rows = [ ]
        for j in data:
            row = [j['project'], j['name'], j['done'], j['total'],
                   j['statisticsFinished'] ]
            rows.append(row)
        response['rows'] = rows
        return response


    def do_POST(self):
        if self.path.startswith("/json-rpc/"):
            self.handleCall()
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
            return False
        return True

    def handleCall(self):
        # JSON RPC request must be in one line o
        request = json.loads(self.rfile.readline())

        if "id" not in request:
            self.exceptBadRequest("""`id` field is missing from JSON RPC request body.
It must be `null` if you want to send notification.""")
            return

        id = request['id']

        if "method" not in request:
            self.exceptBadRequest("`method` field is missing from JSON RPC request body.", id)
            return
        if "params" not in request:
            self.exceptBadRequest("""`params` field is missing from JSON RPC request body.
It must be an empty array if method has no params.""", id)
            return

        methodName = request['method']
        params = request['params']

        if not isinstance(params, type( [] )):
            self.exceptBadRequest("`params` fields must be an array.", id)
            return

        xmlrpc = self.server.rpc_server
        result = "success" # Methods can overwrite this variable.
        try:
            if methodName == "addProject":
                if not self.checkJSONArgsNumber(params, 1): return
                xmlrpc.createProject(params[0])
            elif methodName == "deleteProject":
                if not self.checkJSONArgsNumber(params, 1): return
                xmlrpc.deleteProject(params[0])
            elif methodName == 'addJob':
                if not self.checkJSONArgsNumber(params, 3): return
                xmlrpc.addJob(params[0], params[1], params[2])
            elif methodName == 'deleteJob':
                if not self.checkJSONArgsNumber(params, 2): return
                xmlrpc.deleteJob(params[0], params[1])
            elif methodName == 'runJob':
                if not self.checkJSONArgsNumber(params, 2): return
                xmlrpc.runJob(params[0], params[1])
            else:
                self.sendRPCResponse(None, id, "Unknown method: " + methodName)
                return
        except SocketException, msg:
            self.log_error('Error connecting with RPC-server: %s', msg)
            publicMessage = "Couldn't connect to RPC server."
            self.sendRPCResponse(None, id, publicMessage, 500)

        # If we are here than all was a success.
        self.sendRPCResponse(result, id, None)
