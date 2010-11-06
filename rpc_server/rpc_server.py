#!/usr/bin/python
import logging, couchdb
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

    # Define a handler for console message with mode simple format.
    #console = logging.StreamHandler()
    #console.setFormatter( logging.Formatter('L:%(levelname)-6s %(message)s') )
    logger = logging.getLogger('kts46.rpc_server')
    #logging.getLogger('').addHandler(console)
    logging.info('info')
    logging.warn('warn')

    return (cfg, logger)


def hello(msg):
    "Test method to check that server is working fine."
    return 'Hello you too! This is simple XML-RPC server for kts46.' +\
        '\nYou\'ve said: [' + msg + ']'


def addModel(name, definition):
    server = couchdb.Server('http://127.0.0.1:5984/')
    if name not in server:
        db = server.create(name)
    else:
        raise Exception("Couldn't add model because it already exists.")
    db['model_definition'] = {'name': name, 'yaml': definition }

if __name__ == '__main__':
    cfg, logger = init()

    # Create and configure server.
    address = cfg.get('connection', 'address')
    port = cfg.getint('connection', 'port')
    server = SimpleXMLRPCServer( (address, port), allow_none = True )

    # Register functions.
    server.register_function(hello)
    server.register_function(addModel)

    # Run server.
    logging.warn('Serving...')
    server.serve_forever()
