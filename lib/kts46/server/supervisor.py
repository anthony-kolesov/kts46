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

import logging, time
from datetime import datetime, timedelta
import kts46.utils


class Supervisor:
    """Supervisor that controls tasks state and restarts tasks for which
    workers doesn't respond for required time."""

    def __init__(self, cfg):
        # self.cfg = cfg
        self.log = logging.getLogger(cfg.get('loggers', 'Supervisor'))
        self.server = kts46.utils.getRPCServerProxy(cfg)
        self.checkTimeout = cfg.getint('supervisor', 'checkInterval')
        restartTaskTimeout = cfg.getint('supervisor', 'restartTaskInterval')
        self.restartTaskTimeout = timedelta(seconds=restartTaskTimeout)

    def start(self):
        while True:
            time.sleep(self.checkTimeout)
            self.checkTasks()

    def checkTasks(self):
        tasks = self.server.getCurrentTasks()
        # Get current border of deletion: utcnow() - restartTaskTimeout.
        # utcnow() is used in scheduler for lastUpdate so it here also.

        self.log.info('Starting to check scheduler for staled tasks.')
        deadline = datetime.utcnow() - self.restartTaskTimeout
        for task in tasks:
            lastUpdate = task['lastUpdate'] # is a datetime instance.
            if lastUpdate < deadline:
                # Restart it!
                self.log.info('Restarting staled task for worker %s.', task['workerId'])
                r = self.server.restartTask(task['workerId'], lastUpdate)
                if r:
                    self.log.debug("Task successfully restarted.")
                else:
                    self.log.warning("Scheduler didn't restarted job. Check its log for reason.")
