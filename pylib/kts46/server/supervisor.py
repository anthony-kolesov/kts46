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


import logging
import time
from datetime import datetime, timedelta
from socket import error as SocketException
import kts46.utils
import jsonRpcClient

class Supervisor:
    """Supervisor that controls tasks state and restarts tasks for which
    workers doesn't respond for required time."""

    def __init__(self, cfg):
        # self.cfg = cfg
        self.log = logging.getLogger(cfg.get('loggers', 'Supervisor'))
        #self.server = kts46.utils.getRPCServerProxy(cfg)
        self.jsonrpc = kts46.utils.getJsonRpcClient(cfg)
        self.checkTimeout = cfg.getint('supervisor', 'checkInterval')
        restartTaskTimeout = cfg.getint('supervisor', 'restartTaskInterval')
        self.restartTaskTimeout = timedelta(seconds=restartTaskTimeout)

    def start(self):
        while True:
            time.sleep(self.checkTimeout)
            self.checkTasks()

    def _rpcException(self, descr, error):
        msg = descr +" Message: %s"
        if 'msg' in error:
            msgAdd = error['msg']
        elif 'type' in error:
            msgAdd = error['type']
        else:
            import json
            msgAdd = json.dumps(error)
        self.log.error(msg, msgAdd)
            
    def checkTasks(self):
        self.log.info('Starting to check scheduler for staled tasks.')

        try:
            tasks = self.jsonrpc.getCurrentTasks()
        except SocketException, msg:
            self.log.error("Couldn't connect to RPC server. Message: %s", msg)
            return
        except jsonRpcClient.RPCException as ex:
            self._rpcException("Exception while trying to get current tasks from scheduler.", ex.error)
            return

        # Get current border of deletion: utcnow() - restartTaskTimeout.
        # utcnow() is used in scheduler for lastUpdate so it here also.
        deadline = datetime.utcnow() - self.restartTaskTimeout
        dtFormat = "%Y-%m-%dT%H:%M:%S.%fZ"
        toRestart = filter(lambda task: datetime.strptime(task['sig'], dtFormat) < deadline, tasks)
        #self.log.info('Restarting staled task for worker %s.', task['workerId'])

        if len(toRestart) > 0:
            try:
                r = self.jsonrpc.restartTasks(toRestart)
            except SocketException, msg:
                self.log.error("Couldn't connect to RPC server. Skipping message: %s", msg)
            except jsonRpcClient.RPCException as ex:
                self._rpcException("Exception while trying to restart tasks on scheduler.", ex.error)
                return
            else:
                if r['restarted'] == len(toRestart):
                    self.log.info("All tasks restarted.")
                else:
                    msg = "Scheduler didn't restarted all tasks."\
                        "Check its log for reason."\
                        "Tried to restart %i tasks, but restarted %i."
                    self.log.warning(msg, len(toRestart), r['restarted'])
