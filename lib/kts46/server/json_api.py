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

import logging, BaseHTTPServer, re, json, os.path
import kts46.utils


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

        rpc = self.server.rpc_server
        functionName = match.group(1)
        if functionName == 'projectStatus':
            functionMatch = re.match(r"/api/(\w+)/(\w+)/", self.path)
            projectName = functionMatch.group(2)
            data = rpc.getProjectStatus(projectName)
        elif functionName == 'serverStatus':
            data = rpc.getServerStatus()
        elif functionName == 'addProject' or functionName == 'deleteProject':
            projectNameMatch = re.match(r"/api/(\w+)/(\w+)/", self.path)
            projectName = projectNameMatch.group(2)
            if functionName == 'addProject':
                rpc.createProject(projectName)
            else:
                rpc.deleteProject(projectName)
            data = {'result': 'success'}
        else:
            data = None

        if data is None:
            self.send_response(404)
            self.end_headers()
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(data))

    def do_POST(self):
        self.log_message('POST request')

        match = re.match(r"/api/(\w+)/", self.path)
        functionName = match.group(1)

        success = True
        found = True

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
