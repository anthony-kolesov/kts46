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

import json
import urllib2

class RPCException(Exception):
    def __init__(self, errorObj):
        self.error = errorObj

class Client(object):

    def __init__(self, address, id=0):
        self.address = address
        self.id = id

    def __getattr__(self, name):
        self.id += 1
        return MethodCall(self.address, name, self.id)

class MethodCall(object):

    def __init__(self, address, methodName, id=1):
        self.address = address
        self.name = methodName
        self.id = id

    def __call__(self, *args):
        data = {'method': self.name, 'id': self.id, 'params': args}
        responseStr = urllib2.urlopen(self.address, json.dumps(data)).read()
        response = json.loads(responseStr)
        if response['error'] is not None:
            raise RPCException(response['error'])
        else:
            return response['result']
