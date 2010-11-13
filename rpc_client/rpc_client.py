#!/usr/bin/python
import xmlrpclib, logging, sys
from ConfigParser import SafeConfigParser
from optparse import OptionParser

def init():
    configFiles = ('../config/rpc_client.ini', '../config/common.ini')

    # Configure logging.
    logging.basicConfig(level=logging.INFO,
                        format=cfg.get('log', 'format'),
                        datefmt=cfg.get('log', 'dateFormat'),
                        filename=cfg.get('log', 'filename'),
                        filemode=cfg.get('log', 'filemode'))

    # Define a handler for console message with mode simple format.
    console = logging.StreamHandler()
    console.setFormatter( logging.Formatter(cfg.get('log', 'shortFormat')) )
    logger = logging.getLogger(cfg.get('log', 'loggerName'))
    logger.addHandler(console)

    # Create configuration.
    logger.debug('Reading configuration.')
    cfg = SafeConfigParser()
    cfg.read(configFiles)

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
    host = cfg.get('rpc-client', 'server')
    port = cfg.getint('rpc-server', 'port')
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
        #sp.simulate(modelName, '1')
    elif options.force:
        logger.info('Project exists and --force is selected. Remove current project.')
        sp.deleteProject(modelName)
        sp.createProject(modelName)
        sp.addJob(modelName, modelName, yamlStr)
        sp.simulate(modelName, '1')
    else:
        logger.error(("Couldn't add model with name '%s' to server " +
                     "because model with this name alredy exists.") % modelName)
