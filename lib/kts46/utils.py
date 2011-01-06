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

import logging, logging.handlers, xmlrpclib
from ConfigParser import SafeConfigParser


def getConfiguration(customConfigFiles=[]):
    """Returns ConfigParser for application.

    Loads configuration from default files and custom application files if
    provided.
    """
    configFiles = ['../config/common.ini']
    configFiles.extend(customConfigFiles)
    cfg = SafeConfigParser()
    cfg.read(configFiles)
    return cfg


def configureLogging(cfg):
    "Setups logging module."

    logging.getLogger('').setLevel(logging.INFO)
    logging.basicConfig(format=cfg.get('log', 'format'),
                        datefmt=cfg.get('log', 'dateFormat'))

    # Define a log handler for rotating files.
    rfhandler = logging.handlers.RotatingFileHandler(cfg.get('log', 'filename'),
        maxBytes=cfg.get('log', 'maxBytesInFile'),
        backupCount=cfg.get('log', 'backupCountOfFile'))
    rfhandler.setLevel(logging.INFO)
    rfhandler.setFormatter(logging.Formatter(cfg.get('log', 'format')))
    logging.getLogger('').addHandler(rfhandler)



def getLogger(cfg):
    "Gets logger configured according to data from ConfigParser"
    logger = logging.getLogger(cfg.get('log', 'loggerName'))
    logger.setLevel(logging.INFO)
    return logger

def getRPCServerProxy(cfg):
    # Create RPC proxy.
    host = cfg.get('rpc-server', 'address')
    port = cfg.getint('rpc-server', 'port')
    connString = 'http://{host}:{port}'.format(host=host, port=port)
    proxy = xmlrpclib.ServerProxy(connString)
    return proxy
