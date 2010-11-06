#!/usr/bin/python
import xmlrpclib, logging, sys
from ConfigParser import SafeConfigParser

def init():
    # Configure logging.
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m/%d %H:%M:%S',
                        filename='/tmp/kts46_rpc_client.log',
                        filemode='w')

    # Define a handler for console message with mode simple format.
    console = logging.StreamHandler()
    console.setFormatter( logging.Formatter('L:%(levelname)-6s %(message)s') )
    logger = logging.getLogger('kts46.rpc_client')
    logger.addHandler(console)

    # Create configuration.
    logger.debug('Reading configuration.')
    cfg = SafeConfigParser()
    cfg.read(('rpc_client.ini',))

    return (cfg, logger)

cfg, logger = init()

# Create proxy.
host = cfg.get('connection', 'server')
port = cfg.getint('connection', 'port')
connString = 'http://%s:%i' % (host, port)
logger.info('Connecting to server %s' % connString)
sp = xmlrpclib.ServerProxy(connString)

# Say hello and print available functions.
print( sp.hello('Hello Mr. Server!') )

# Model file.
modelFile = sys.argv[1]
modelName = sys.argv[2]
logger.info('Working with model file: %s' % modelFile)
fp = open(modelFile, 'r')
yamlStr = fp.read(-1)
fp.close()
logger.info('Adding model to database.')
sp.addModel(modelName, yamlStr)
