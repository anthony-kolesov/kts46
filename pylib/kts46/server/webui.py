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

import csv
import gviz_api
import httplib
import json
import logging
import mimetypes
import re
import urlparse
from cStringIO import StringIO
from socket import error as SocketException
import kts46.rpcClient

# Add MIME types
mimetypes.add_type("text/csv", ".csv", True) # True to add to official types.
mimetypes.add_type("application/json", ".json", True) # True to add to official types.

class DataAPIHandler(object):

    def __init__(self, statusServer):
        self.statusServer = statusServer
        self.logger = logging.getLogger('kts46.server.WebUI.data')


    def _error(self, code, startResponse):
        startResponse(str(code) + ' ' + httplib.responses[code], [('"Content-Type', 'text/plain')])


    def _missingParam(self, startResponse, paramName):
        self._error(httplib.NOT_FOUND, startResponse)
        return paramName.join(("Required parameter `", "` is missing.\n"))


    def handle(self, environ, startResponse):
        # Parse query.
        params = urlparse.parse_qs(environ["QUERY_STRING"])

        # Get method name
        if "method" not in params:
            return self._missingParam(startResponse, "method")
        methodName = params["method"][0]

        # Get parameters.
        del params["method"]

        # Call required method.
        if methodName == "serverStatus":
            if "tqx" not in params:
                return self._missingParam(startResponse, "tqx")
            result = self.serverStatusByGoogle(params["tqx"][0])
        elif methodName == "jobStatistics":
            if "p" not in params: return self._missingParam(startResponse, "p")
            if "j" not in params: return self._missingParam(startResponse, "j")
            result = self.jobStatistics(params['p'][0], params['j'][0])
        elif methodName == "modelDescription":
            if "p" not in params: return self._missingParam(startResponse, "p")
            if "j" not in params: return self._missingParam(startResponse, "j")
            result = self.modelDescription(params['p'][0], params['j'][0])
        elif methodName == "modelState":
            if "p" not in params: return self._missingParam(startResponse, "p")
            if "j" not in params: return self._missingParam(startResponse, "j")
            if "t" not in params: return self._missingParam(startResponse, "t")
            if re.match("(\d+)|(\d*\.\d+)", params["t"][0]):
                self._error(httplib.NOT_FOUND)
                return "Invalid `time` format: must be float number."
            result = self.modelState(params['p'][0], params['j'][0], float(params['t'][0]))
        else:
            self._error(httplib.NOT_FOUND, startResponse)
            return "Unknown method: " + methodName + "\n"

        # Convert output to apropriate format.
        type = "json"
        mimeType = mimetypes.types_map['.json']
        if "type" in params:
            if params["type"][0] == "jsonp":
                if "callback" not in params:
                    return self._missingParam(startResponse, "callback")
                type = "jsonp"
                callback = params["callback"][0]
                mimeType = mimetypes.types_map['.js']
            elif params["type"][0] == "csv":
                type = "csv"
                mimeType = mimetypes.types_map['.csv']
            elif params["type"][0] == "tsv":
                type = "tsv"
                mimeType = mimetypes.types_map['.tsv']
        elif methodName == "serverStatus":
            mimeType = mimetypes.types_map['.js']

        startResponse(str(httplib.OK) + ' ' +httplib.responses[httplib.OK],
                     [("Content-Type", mimeType)])
        if methodName != "serverStatus":
            if type == "json":
                output = json.dumps(result)
            elif type == "jsonp":
                output = "".join((callback, "(", json.dumps(result), ");"))
            elif type == "csv" or type == "tsv":
                delim = "," if type == "csv" else "\t"
                with StringIO() as outputIO:
                    writer = csv.DictWriter(outputIO, [], delimeter=delim,
                                            qouting=csv.QUOTE_MINIMAL)
                    writer.writerows(result)
                    output = outputIO.getvalue()
        else:
            output = str(result)

        # Return output.
        return output

    def serverStatusByGoogle(self, tqx):
        data = self.statusServer.getServerStatus()
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

    def jobStatistics(self, project, job):
        return self.statusServer.getJobStatistics(project, job, False)

    def modelDescription(self, project, job):
        return self.statusServer.getModelDescription(project, job)

    def modelState(self, project, job, time):
        return self.statusServer.getModelState(project, job, time)

class ManagementAPIHandler(object):

    def __init__(self, cfg, dbServer, statusServer):
        self.jsonrpc = kts46.rpcClient.getJsonRpcClient(cfg)
        self.dbServer = dbServer
        self.statusServer = statusServer
        self.logger = logging.getLogger('kts46.server.WebUI.management')


    def sendRPCResponse(self, response, result, id, error, httpcode=200):
        response(str(httpcode) + ' ' + httplib.responses[httpcode], [
            ('Content-Type', mimetypes.types_map[".json"]) ])
        return json.dumps({'result':result, 'id':id, 'error': error})


    def exceptBadRequest(self, response,  msg, id=None):
        return self.sendRPCResponse(response, None, id, msg, httplib.BAD_REQUEST)


    def checkJSONArgsNumber(self, response, params, amount):
        if len(params) != amount:
            msg = "Provided number of parameters is invalid. Required number of params: {0}, but has: {1}."
            return self.exceptBadRequest(response, msg.format(amount, len(params)), id)
        return None


    def handle(self, environ, response):
        # JSON RPC request must be in one line.
        try:
            request = json.loads(environ["wsgi.input"].readline())
        except ValueError as err:
            return self.exceptBadRequest(response, err.message)

        if "id" not in request:
            return self.exceptBadRequest(response,
                """`id` field is missing from JSON RPC request body.
It must be `null` if you want to send notification.""")

        id = request["id"]

        if "method" not in request:
            return self.exceptBadRequest(response,
                "`method` field is missing from JSON RPC request body.", id)
        if "params" not in request:
            return self.exceptBadRequest(response,
                """`params` field is missing from JSON RPC request body.
It must be an empty array if method has no params.""", id)

        methodName = request['method']
        params = request['params']

        if not isinstance(params, type( [] )):
            return self.exceptBadRequest(response,
                                        "`params` fields must be an array.", id)

        result = "success" # Methods can overwrite this variable.
        try:
            if methodName == "addProject":
                test = self.checkJSONArgsNumber(response, params, 1)
                if test is not None:
                    return test
                self.dbServer.createProject(params[0])
            elif methodName == "deleteProject":
                test = self.checkJSONArgsNumber(response, params, 1)
                if test is not None:
                    return test
                self.dbServer.deleteProject(params[0])
            elif methodName == 'addJob':
                test = self.checkJSONArgsNumber(response, params, 3)
                if test is not None:
                    return test
                self.dbServer.addJob(params[0], params[1], params[2])
            elif methodName == 'deleteJob':
                test = self.checkJSONArgsNumber(response, params, 2)
                if test is not None:
                    return test
                self.dbServer.deleteJob(params[0], params[1])
            elif methodName == 'listJobStatistics':
                test = self.checkJSONArgsNumber(response, params, 1)
                if test is not None:
                    return test
                result = []
                for a in params[0]:
                    result.append(self.statusServer.getJobStatistics(a['p'],a['j'], False))
                    result[-1]['project'] = a['p']
                    result[-1]['job'] = a['j']
            elif methodName == 'runJob':
                test = self.checkJSONArgsNumber(response, params, 2)
                if test is not None:
                    return test
                try:
                    self.jsonrpc.addTask(params[0], params[1])
                except jsonRpcClient.RPCException as ex:
                    self.logger.warning("Scheduler returned error: %s.", ex.error['type']);
                    return self.sendRPCResponse(response, None, id, ex.error)
            else:
                return self.sendRPCResponse(response, None, id, "Unknown method: " + methodName)
        except SocketException, msg:
            self.log_error('Error connecting with RPC-server: %s', msg)
            publicMessage = "Couldn't connect to RPC server."
            return self.sendRPCResponse(response, None, id, publicMessage, httplib.INTERNAL_SERVER_ERROR)

        # If we are here than all was a success.
        return self.sendRPCResponse(response, result, id, None)
