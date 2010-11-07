#!/usr/bin/python
import logging, couchdb, logging.handlers
from SimpleXMLRPCServer import SimpleXMLRPCServer
from ConfigParser import SafeConfigParser

def init():
    """Initializes server infrastructure. Returns (SafeConfigParser, logger)."""
    # Create configuration.
    logging.debug('Reading configuration.')
    cfg = SafeConfigParser()
    cfg.read(('rpc_server.ini', '../stats/basicStats.ini'))

    # Configure logging.
    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m/%d %H:%M:%S',
                    filename='/tmp/kts46_rpc_server.log',
                    filemode='w')

    # Define a log handler for rotating files.
    rfhandler = logging.handlers.RotatingFileHandler(cfg.get('log', 'filename'),
        maxBytes=cfg.get('log', 'maxBytesInFile'),
        backupCount=cfg.get('log', 'backupCountOfFile'))
    rfhandler.setLevel(logging.INFO)
    logging.getLogger('').addHandler(rfhandler)

    logger = logging.getLogger('kts46.rpc_server')

    return (cfg, logger)


def hello(msg):
    "Test method to check that server is working fine."
    return '''Hello you too! This is simple XML-RPC server for kts46.
            You\'ve said: [''' + msg + ']'

class CouchDBProxy:

    def __init__(self, cfg):
        self.cfg = cfg
        self.logger = logging.getLogger('kts46.rpc_server.couchdb')
        self.server = couchdb.Server(cfg.get('couchdb', 'dbaddress'))

    def addModel(self, modelName, definition):
        "Adds specified model to the database if it doesn't already exists."
        if modelName not in self.server:
            db = self.server.create(modelName)
            db['model_definition'] = {'name': modelName, 'yaml': definition }
        else:
            raise Exception("Couldn't add model because it already exists.")

    def modelExists(self, modelName):
        "Checks whether model with provided name already exists."
        return modelName in self.server
    
    def deleteModel(self, modelName):
        "Deletes model with specified name if it exists. Otherwise creates an exception."
        if modelName in self.server:
            self.logger.info("Deleting model with name '%s'." % modelName)
            del self.server[modelName]
        else:
            raise Exception("""Couldn't delete model with name '%s' because it
                             doesn't exists.""" % modelName)
            

if __name__ == '__main__':
    cfg, logger = init()

    # Create and configure server.
    address = cfg.get('connection', 'address')
    port = cfg.getint('connection', 'port')
    server = SimpleXMLRPCServer( (address, port), allow_none = True )

    # Register functions.
    couchdbProxy = CouchDBProxy(cfg)
    server.register_function(hello)
    server.register_instance(couchdbProxy)

    # Run server.
    logging.warn('Serving...')
    server.serve_forever()
