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

import Queue, threading
from multiprocessing.managers import BaseManager

class Scheduler(BaseManager):
    pass

class Dummy:
    def send(self, param): pass

def shutdown():
    server.shutdown( Dummy() )

def runJob(projectName, jobName):
    print('add job: %s.%s' %(projectName, jobName))
    queue.put({'p':projectName, 'j':jobName})

def getJob():
    print('get job')
    return queue.get()

queue = Queue.Queue()
Scheduler.register('get_queue', callable=lambda:queue)
Scheduler.register('shutdown', callable=shutdown)
Scheduler.register('runJob', callable=runJob)
Scheduler.register('getJob', callable=getJob)

manager = Scheduler(address=('', 46211), authkey='anthony')

server = manager.get_server()
server.serve_forever()
