#!/usr/bin/python
import logging
from SimpleXMLRPCServer import SimpleXMLRPCServer
from ConfigParser import SafeConfigParser

def init():
    """Initializes server infrastructure. Returns (SafeConfigParser, logger)."""
    # Create configuration.
    logging.debug('Reading configuration.')
    cfg = SafeConfigParser()
    cfg.read(('rpc_server.ini',))

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
    return 'Hello you too! This is simple XML-RPC server for kts46.' +\
        '\nYou\'ve said: [' + msg + ']'


if __name__ == '__main__':
    cfg, logger = init()

    # Create and configure server.
    address = cfg.get('connection', 'address')
    port = cfg.getint('connection', 'port')
    server = SimpleXMLRPCServer( (address, port) )

    # Register functions.
    server.register_function(hello)

    # Run server.
    logging.warn('Serving...')
    server.serve_forever()
