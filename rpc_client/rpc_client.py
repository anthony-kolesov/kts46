#!/usr/bin/python
import xmlrpclib, logging, sys
from ConfigParser import SafeConfigParser
from optparse import OptionParser

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

if __name__ == '__main__':
    cfg, logger = init()
    
    usage = "usage: %prog [options] <modelFile> <modelName>"
    cmdOpts = OptionParser(usage=usage)
    cmdOpts.add_option('-f', '--force', action='store_true', dest='force',
                       default=False,
                       help='Force creation of new model if it already exists.')
    options, args = cmdOpts.parse_args(sys.argv[1:])
    if len(args) != 2:
        cmdOpts.error('Invalid number of arguments. Must be 2. See -h for help.')
    

    # Create proxy.
    host = cfg.get('connection', 'server')
    port = cfg.getint('connection', 'port')
    connString = 'http://%s:%i' % (host, port)
    logger.info('Connecting to server %s' % connString)
    sp = xmlrpclib.ServerProxy(connString)

    # Say hello and print available functions.
    print( sp.hello('Hello Mr. Server!') )

    # Model file.
    modelFile = args[0]
    modelName = args[1]
    logger.info('Working with model file: %s' % modelFile)
    fp = open(modelFile, 'r')
    yamlStr = fp.read(-1)
    fp.close()
    logger.info('Checking whether project already exists on server.')
    if not sp.projectExists(modelName):
        logger.info('Adding project to database.')
        sp.createProject(modelName)
        sp.addJob(modelName, modelName, yamlStr)
        #sp.simulate(modelName, 'j1', 30, 0.04)
    elif options.force:
        logger.info('Project exists and --force is selected. Remove current project.')
        sp.deleteProject(modelName)
        sp.createProject(modelName)
        sp.addJob(modelName, modelName, yamlStr)
        #sp.simulate(modelName, 'j1', 30, 0.1)
    else:
        logger.error(("Couldn't add model with name '%s' to server " +
                     "because model with this name alredy exists.") % modelName)