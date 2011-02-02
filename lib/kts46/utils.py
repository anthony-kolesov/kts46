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

"Some useful function."

import logging, logging.handlers
import xmlrpclib
from ConfigParser import SafeConfigParser
from datetime import timedelta

def getConfiguration(customConfigFiles=[]):
    """Returns ``SafeConfigParser`` for application. Loads configuration from
    default files and custom application files if they are provided.

    :param customConfigFiles:
        List of paths to additional ocnifguration files. Values from this files
        will override those from default files.
    :return: application confguration.
    """
    configFiles = ['../config/default.ini', '../config/local.ini']
    configFiles.extend(customConfigFiles)
    cfg = SafeConfigParser()
    cfg.read(configFiles)
    return cfg


def configureLogging(cfg):
    """Confugres logging module for this application.

    :param cfg: Application configuration.
    :type cfg: ConfigParser
    """
    logging.getLogger('').setLevel(logging.INFO)

    # Define a log handler for console.
    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.INFO)
    consoleHandler.setFormatter(logging.Formatter(cfg.get('log', 'format')))
    logging.getLogger('kts46').addHandler(consoleHandler)

    # Define a log handler for rotating files.
    rfhandler = logging.handlers.RotatingFileHandler(cfg.get('log', 'filename'),
        maxBytes=cfg.get('log', 'maxBytesInFile'),
        backupCount=cfg.get('log', 'backupCountOfFile'))
    rfhandler.setLevel(logging.INFO)
    rfhandler.setFormatter(logging.Formatter(cfg.get('log', 'format')))
    logging.getLogger('').addHandler(rfhandler)


def getLogger(cfg):
    """Gets logger configured according to data from ConfigParser.

    :param cfg: Application configuration.
    :type cfg: ConfigParser
    :returns: Logger for this application.
    """
    logger = logging.getLogger(cfg.get('log', 'loggerName'))
    logger.setLevel(logging.INFO)
    return logger


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

    
def timedelta2str(data):
    # Only days, seconds and microseconds are stored internally.
    return u'{0}d{1}s{2}'.format(data.days, data.seconds, data.microseconds)

def str2timedelta(value):
    days, rest = value.split('d')
    seconds, mcs = rest.split('s')
    return timedelta(days=int(days), seconds=int(seconds), microseconds=int(mcs))
    