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


class MissingParameterException(Exception):
    def __init__(self, message):
        super(Exception, self).__init__()
        self.message = message
    def __str__(self):
        return self.message.join( ("Required parameter `", "` is missing.") )


class DataAPIHandler(object):

    def __init__(self, statusServer):
        self.statusServer = statusServer
        self.logger = logging.getLogger('kts46.server.WebUI.data')
        self.serverStatusGvizSschema = {
            "project":("string", "Project"),
            "name":("string", "Job"),
            "totalSteps": ("number", "Total states"),
            "done": ("number", "Done steps"),
            "basicStatistics":("boolean", "Basic stats"),
            "idleTimes":("boolean", "Idle times"),
            "throughput":("boolean", "Throughput"),
            "fullStatistics":("boolean", "All stats")
        }
        self.serverStatusColumnsOrder = ("project", "name", "done", "totalSteps",
                "basicStatistics", "idleTimes", "throughput", "fullStatistics")


    def _error(self, code, startResponse):
        self._startResponse(code, startResponse)


    def _startResponse(self, httpCode, response):
        response(' '.join((str(httpCode), httplib.responses[httpCode])),
                 [('"Content-Type', 'text/plain')])


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

        fields = []

        # Call required method.
        try:
            if methodName == "serverStatus":
                result = self.serverStatusByGoogle(params)
            elif methodName == "jobStatistics":
                result = self.jobStatistics(params)
            elif methodName == "modelDescription":
                result = self.modelDescription(params)
            elif methodName == "modelState":
                result = self.modelState(params)
            elif methodName == "listJobStatistics":
                result = self.listJobStatistics(params)
                fields = ["project", "job", "average", "stdeviation", "averageSpeed",
                      "averageIdleTime", "startThroughput", "endThroughput"]
            else:
                self._startResponse(httplib.NOT_FOUND, startResponse)
                return methodName.join(("Unknown method: ","\n"))
        except MissingParameterException as ex:
            self._startResponse(httplib.NOT_FOUND, startResponse)
            return ex.message
        except ValueError as ex:
            self._startResponse(httplib.BAD_REQUEST, startResponse)
            return ex.message
        except KeyError as ex:
            self._startResponse(httplib.NOT_FOUND, startResponse)
            return ex.message

        # Convert output to apropriate format.
        try:
            type, mimeType = self.getType(params)
        except MissingParameterException as ex:
            self._startResponse(httplib.NOT_FOUND, startResponse)
            return ex.message

        startResponse(str(httplib.OK) + ' ' +httplib.responses[httplib.OK],
                     [("Content-Type", mimeType)])
        if methodName != "serverStatus":
            if type == "json":
                output = json.dumps(result)
            elif type == "jsonp":
                output = "".join((callback, "(", json.dumps(result), ");"))
            elif type == "csv" or type == "tsv":
                if len(fields) == 0:
                    self._error(httplib.BAD_REQUEST, startResponse)
                    return "This method doesn't support tabular response."

                delim = "," if type == "csv" else "\t"
                outputIO = StringIO()
                writer = csv.DictWriter(outputIO, fields, delimiter=delim, quoting=csv.QUOTE_MINIMAL)
                writer.writerows(result)
                output = outputIO.getvalue()
        else:
            output = str(result)

        # Return output.
        return output


    def getType(self, params):
        "Gets type of output data (json, jsonp, csv, tsv). Returns (type, mimeType)."
        type = "json"
        mimeType = mimetypes.types_map['.json']
        if "type" in params:
            if params["type"][0] == "jsonp":
                if "callback" not in params:
                    raise MissingParameterException("callback")
                type = "jsonp"
                mimeType = mimetypes.types_map['.js']
            elif params["type"][0] == "csv":
                type = "csv"
                mimeType = mimetypes.types_map['.csv']
            elif params["type"][0] == "tsv":
                type = "tsv"
                mimeType = mimetypes.types_map['.tsv']
        elif methodName == "serverStatus":
            type = "jsonp"
            mimeType = mimetypes.types_map['.js']
    return (type, mimeType)

    def serverStatusByGoogle(self, params):
        if "tqx" not in params: raise MissingParameterException("tqx")
        tqx = params["tqx"][0]

        data = self.statusServer.getServerStatus()
        table = gviz_api.DataTable(self.serverStatusGvizSschema)
        table.LoadData(data)
        return table.ToResponse(columns_order=self.serverStatusColumnsOrder, tqx=tqx)


    def jobStatistics(self, params):
        if "p" not in params: raise MissingParameterException("p")
        if "j" not in params: raise MissingParameterException("j")
        return self.statusServer.getJobStatistics(params['p'][0], params['j'][0], False)


    def modelDescription(self, params):
        if "p" not in params: raise MissingParameterException("p")
        if "j" not in params: raise MissingParameterException("j")
        return self.statusServer.getModelDescription(params['p'][0], params['j'][0])


    def modelState(self, params):
        if "p" not in params: raise MissingParameterException("p")
        if "j" not in params: raise MissingParameterException("j")
        if "t" not in params: raise MissingParameterException("t")
        if not re.match("^(\d*\.)?\d+$", params["t"][0]):
            raise ValueError("Invalid `time` format: must be float number.")

        return self.statusServer.getModelState(params['p'][0], params['j'][0], params['t'][0])


    def listJobStatistics(self, params):
        if "q" not in params: raise MissingParameterException("q")
        query = params["q"][0]
        projectsAsStrings = query.split(" ")
        projects = {}
        for pj in projectsAsStrings:
            try:
                projectName, jobs = pj.split(":")
            except ValueError:
                raise ValueError("Couldn't separate project name from job names.")
            projects[projectName] = jobs.split(",")

        result = []
        for project, jobs in projects.iteritems():
            for job in jobs:
                stat = self.statusServer.getJobStatistics(project, job, False)
                format = {
                    "project": project,
                    "job": job,
                    "average": stat["average"],
                    "stdeviation": stat["stdeviation"],
                    "averageSpeed": stat["averageSpeed"],
                    "averageIdleTime": stat["idleTimes"]["average"],
                    "startThroughput": stat["throughput"][0]["rate"],
                    "startThroughput": stat["throughput"][-1]["rate"]
                }
                result.append(format)
        return result


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
