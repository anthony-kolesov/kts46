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

"Methods to get RPC clients."

import xmlrpclib
import jsonRpcClient

def getRPCServerProxy(cfg):
    """Create an RPC proxy to server.

    :param cfg: Application configuration.
    :type cfg: ConfigParser
    :returns: Proxy to an XML-RPC server.
    :rtype: xmlrpclib.ServerProxy
    """
    host = cfg.get('rpc-server', 'address')
    port = cfg.getint('rpc-server', 'port')
    connString = 'http://{host}:{port}'.format(host=host, port=port)
    proxy = xmlrpclib.ServerProxy(connString)
    return proxy


def getJsonRpcClient(cfg):
    """Create a JSON-RPC client.

    :param cfg: Application configuration.
    :type cfg: ConfigParser
    :returns: Proxy to a JSON-RPC server.
    :rtype: jsonRpcClient.Client
    """
    host = cfg.get('JSON-RPC Server', 'host')
    port = cfg.getint('JSON-RPC Server', 'port')
    path = cfg.get('JSON-RPC Server', 'path')
    connString = 'http://{host}:{port}{path}'.format(host=host, port=port, path=path)
    return jsonRpcClient.Client(connString)
