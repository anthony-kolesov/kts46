#!/usr/bin/python
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


import logging, sys
# Project imports
PROJECT_LIB_PATH = '../lib/'
if PROJECT_LIB_PATH not in sys.path:
    sys.path.append(PROJECT_LIB_PATH)
from kts46.statisticsServer import StatisticsServer
import kts46.utils
from kts46.CouchDBStorage import CouchDBStorage

cfg = kts46.utils.getConfiguration()
kts46.utils.configureLogging(cfg)
log = logging.getLogger('kts46.probe')
storage = CouchDBStorage(cfg.get('couchdb', 'dbaddress'))

s = StatisticsServer(cfg)
s.calculate(storage['model_v2']['exp_1_1'])
