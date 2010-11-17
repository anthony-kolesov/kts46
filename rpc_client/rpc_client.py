#!/usr/bin/python
"""
License:
   Copyright 2010 Anthony Kolesov

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

import xmlrpclib, logging, sys
from ConfigParser import SafeConfigParser
from optparse import OptionParser

def init():
    configFiles = ('../config/rpc_client.ini', '../config/common.ini')

    # Create configuration.
    cfg = SafeConfigParser()
    cfg.read(configFiles)

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

    return (cfg, logger)

if __name__ == '__main__':
    cfg, logger = init()

    # create project
    # delete project
    # add job
    # delete job
    # run job

    usage = "usage: %prog [options] <action>"
    epilog = """<action> could be: createProject (crp), deleteProject (delp)
addJob (a), deleteJob (delj), runJob (r), shutdown."""
    cmdOpts = OptionParser(usage=usage, epilog=epilog)
    cmdOpts.add_option('-p', '--project', action='store', dest='proj', default='',
                       help='Project name. This option is required.')
    cmdOpts.add_option('-j', '--job', action='store', dest='job', default='',
                       help='Job name.')
    cmdOpts.add_option('-f', '--file', action='store', dest='file', default='',
                       help='Path to file with job definition.')

    options, args = cmdOpts.parse_args(sys.argv[1:])
    if len(args) != 1:
        cmdOpts.error('There must be one and only one positional argument of action.')
    if len(options.proj) < 1 and args[0] != 'shutdown':
        cmdOpts.error('Project name must be specified. See options -p and --project')

    # Create RPC proxy.
    host = cfg.get('rpc-client', 'server')
    port = cfg.getint('rpc-server', 'port')
    connString = 'http://%s:%i' % (host, port)
    logger.info('Connecting to server %s' % connString)
    sp = xmlrpclib.ServerProxy(connString)

    # Do action.
    if args[0] == 'shutdown':
        sp.shutdown()
        del sp
    elif args[0] == 'crp' or args[0] == 'createProject':
        logger.info('Creating project: %s' % options.proj)
        if sp.projectExists(options.proj):
            msg = "Couldn't create project '%s', because it already exists."
            logger.error(msg % options.proj)
        else:
            sp.createProject(options.proj)
            if not sp.projectExists(options.proj):
                logger.warning("Error adding project '%s'." % options.proj)
    elif args[0] == 'delp' or args[0] == 'deleteProject':
        logger.info('Deleting project: %s' % options.proj)
        if sp.projectExists(options.proj):
            sp.deleteProject(options.proj)
            if sp.projectExists(options.proj):
                logger.warning("Error deleting project '%s'." % options.proj)
        else:
            msg = "Couldn't delete project '%s' that doesn't exists."
            logger.error(msg % options.proj)
    elif args[0] == 'a' or args[0] == 'addJob':
        if len(options.job) == 0: cmdOpts.error('Job name must be specified.')
        if len(options.file) == 0: cmdOpts.error('Job file must be specified.')
        logger.info("Adding job '%s' to project '%s' from file '%s'" %
                    (options.job, options.proj, options.file))

        if not sp.projectExists(options.proj):
            msg = "Couldn't add job to project '%s' because project doesn't exists."
            logger.error(msg % options.proj)
            sys.exit(1)
        if sp.jobExists(options.proj, options.job):
            msg = "Couldn't add job '%s' to project '%s' because job already exists."
            logger.error(msg % (options.job, options.proj))
            sys.exit(1)

        f = open(options.file, 'r')
        yamlStr = f.read(-1)
        f.close()

        sp.addJob(options.proj, options.job, yamlStr)
        if not sp.jobExists(options.proj, options.job):
            msg = "Error adding job '%s' to project '%s'."
            logger.warning(msg % (options.job, options.proj))

    elif args[0] == 'delj' or args[0] == 'deleteJob':
        if len(options.job) == 0: cmdOpts.error('Job name must be specified.')
        logger.info("Deleting job '%s' from project '%s'" % (options.job, options.proj))

        if not sp.projectExists(options.proj):
            msg = "Couldn't delete job from project '%s' because project doesn't exists."
            logger.error(msg % options.proj)
        elif not sp.jobExists(options.proj, options.job):
            msg = "Couldn't delete job '%s' from project '%s' because job doesn't exists."
            logger.error(msg % (options.job, options.proj))
        else:
            sp.deleteJob(options.proj, options.job)
            if sp.jobExists(options.proj, options.job):
                msg = "Error deleting job '%s' from project '%s'."
                logger.warning(msg % (options.job, options.proj))
    elif args[0] == 'r' or args[0] == 'runJob':
        if len(options.job) == 0: cmdOpts.error('Job name must be specified.')
        logger.info("Running job '%s' from project '%s'" % (options.job, options.proj))

        if not sp.projectExists(options.proj):
            msg = "Couldn't run job from project '%s' because project doesn't exists."
            logger.error(msg % options.proj)
        elif not sp.jobExists(options.proj, options.job):
            msg = "Couldn't run job '%s' from project '%s' because job doesn't exists."
            logger.error(msg % (options.job, options.proj))
        else:
            sp.runJob(options.proj, options.job)

    # Say hello.
    # print( sp.hello('Hello Mr. Server!') )
