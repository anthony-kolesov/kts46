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

import logging, BaseHTTPServer, re


class JSONApiServer:
    "Provides HTTP server that provides control over simulation with JSON API."

    def __init__(self, cfg):
        pass

    def server_forever(self):
        server_address = ('', 46211)
        httpd = BaseHTTPServer.HTTPServer(server_address, JSONApiRequestHandler)
        httpd.serve_forever()


class JSONApiRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):
        match = re.match(r"/api/(\w+)/(\w+)/", self.path)
        if match is None:
            self.send_response(404)
            self.end_headers()
            return

        function = match.group(1)
        p = match.group(2)

        self.send_response(200)
        self.end_headers()
        self.wfile.write("funct={0}, arg={1}".format(function, p))

