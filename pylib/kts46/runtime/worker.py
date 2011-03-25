#!/usr/bin/python

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

"""Runs all kts46 server processes."""

import logging
import sys
from ConfigParser import SafeConfigParser
from optparse import OptionParser
# Project imports
import kts46.utils
from kts46.server.worker import Worker


def configureCmdOptions():
    usage = "usage: %prog [options]"

    cmdOpts = OptionParser(usage=usage)
    cmdOpts.add_option('-i', '--worker-id', action='store', dest='wid', default=None,
                       help='Worker id. Must be unique in a network of workers.')
    cmdOpts.add_option('--cfg', action='store', dest='cfg', default='',
                       help="Configuration file that will override default.ini and local.ini." )
    cmdOpts.add_option('-q', '--quite', action='store_true', dest='quite',
                       help='Suppress all output to console.')

    return cmdOpts.parse_args(sys.argv[1:])


if __name__ == '__main__':
    options, args = configureCmdOptions()

    # Create ConfigParser
    configFiles = []
    if len(options.cfg) != 0: configFiles.append(options.cfg)
    cfg = kts46.utils.getConfiguration(configFiles)
    if options.quite is not None:
        cfg.set('log', 'quite', str(options.quite))

    # Logging
    kts46.utils.configureLogging(cfg)
    logger = logging.getLogger(cfg.get('loggers', 'Node'))

    # Psyco JIT.
    if cfg.getboolean('node', 'enablePsyco'):
        import psyco
        psyco.full()

    worker = Worker(cfg, id)
    worker.run()
