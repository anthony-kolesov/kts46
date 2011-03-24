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

from cStringIO import StringIO
import csv
import gviz_api
import httplib
import json
import logging
import mimetypes
import re
import urlparse
import kts46.rpcClient

class DataAPIHandler(object):

    def __init__(self, cfg):
        self.xmlrpc = kts46.rpcClient.getRPCServerProxy(cfg)
        self.jsonrpc = kts46.rpcClient.getJsonRpcClient(cfg)
        #self.cfg = cfg
        self.logger = logging.getLogger('kts46.server.WebUI')
        # Add MIME types
        mimetypes.add_type("text/csv", ".csv", True) # True to add to official types.
        mimetypes.add_type("application/json", ".json", True) # True to add to official types.


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
            result = self.serverStatusByGoogle(params["tqx"])
        elif methodName == "jobStatistics":
            if "p" not in params: return self._missingParam(startResponse, "p")
            if "j" not in params: return self._missingParam(startResponse, "j")
            result = self.jobStatistics(params['p'], params['j'])
        elif methodName == "modelDescription":
            if "p" not in params: return self._missingParam(startResponse, "p")
            if "j" not in params: return self._missingParam(startResponse, "j")
            result = self.modelDescription(params['p'], params['j'])
        elif methodName == "modelState":
            if "p" not in params: return self._missingParam(startResponse, "p")
            if "j" not in params: return self._missingParam(startResponse, "j")
            if "t" not in params: return self._missingParam(startResponse, "t")
            if re.match("(\d+)|(\d*\.\d+)", params["t"]):
                self._error(httplib.NOT_FOUND)
                return "Invalid `time` format: must be float number."
            result = self.modelState(params['p'], params['j'], float(params['t']))
        else:
            self._error(httplib.NOT_FOUND, startResponse)
            return "Unknown method: " + methodName + "\n"

        # Convert output to apropriate format.
        type = "json"
        mimeType = mimetypes.types_map['.json']
        if "type" in params:
            if params["type"] == "jsonp":
                if "callback" not in params:
                    return self._missingParam(startResponse, "callback")
                type = "jsonp"
                callback = params["callback"]
                mimeType = mimetypes.types_map['.js']
            elif params["type"] == "csv":
                type = "csv"
                mimeType = mimetypes.types_map['.csv']
            elif params["type"] == "tsv":
                type = "tsv"
                mimeType = mimetypes.types_map['.tsv']

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
            output = result

        # Return output.
        return output

    def serverStatusByGoogle(self, tqx):
        data = self.xmlrpc.getServerStatus()
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
        return self.xmlrpc.getJobStatistics(project, job, False)

    def modelDescription(self, project, job):
        return self.xmlrpc.getModelDescription(project, job)

    def modelState(self, projectName, jobName, time):
        return self.xmlrpc.getModelState(project, job, time)
