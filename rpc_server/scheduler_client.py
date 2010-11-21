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

import sys, Queue
from multiprocessing.managers import BaseManager

class Scheduler(BaseManager):
    pass

Scheduler.register('get_queue')
Scheduler.register('shutdown')
Scheduler.register('runJob')
m = Scheduler(address=('localhost', 46211), authkey='anthony')
m.connect()
m.runJob(sys.argv[1], sys.argv[2])
