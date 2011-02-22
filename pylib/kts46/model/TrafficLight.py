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

from random import random
from datetime import timedelta
from uuid import uuid4
import kts46.utils

class SimpleSemaphore(object):
    """Simple semaphore that works in one direction.

    Duration of green and red lights states are setted separatly.
    They are stored as datetime.timedelta type, but you can just a number, it
    will be used as a number of seconds in conversion. Id is always converted to
    unicode.
    """

    __green_state = "g"
    __red_state = "r"

    def __init__(self, id=None, position=0, greenDuration=5, redDuration=5):
        """Creates a new simple semaphore."""
        self.id = str(id if (id is not None) else uuid4())
        self.position = position
        self.lastSwitchTime = timedelta()
        # Original state is random.
        self.state = SimpleSemaphore.__red_state if random() > 0.5 else SimpleSemaphore.__green_state
        self.greenDuration = 5
        self.redDuration = 5

    def switch(self, currentTime):
        "Switches semaphore to the other state and records current time."
        if self.state == SimpleSemaphore.__green_state:
            self.state = SimpleSemaphore.__red_state
        else:
            self.state = SimpleSemaphore.__green_state
        self.lastSwitchTime = currentTime

    @property
    def isGreen(self):
        return self.state == SimpleSemaphore.__green_state

    def getNextSwitchTime(self):
        if self.isGreen:
            addTime = self.greenDuration
        else:
            addTime = self.redDuration
        return self.lastSwitchTime + addTime

    def getDescriptionData(self):
        return {#'id': self.id,
                'position': self.position,
                'green': self.greenDuration,
                'red': self.redDuration
        }

    def getStateData(self):
        return {
            'state': self.state,
            'lastSwitchTime': kts46.utils.timedelta2str(self.lastSwitchTime)
        }

    # Little metaprogramming magic, so it is possible to set duration as float
    # (in seconds). Also store in unicode explicitly.
    def __setattr__(self, name, value):
        effValue = value
        if ((name == "greenDuration" or name == "redDuration") and
                not isinstance(value, timedelta)):
            effValue = timedelta(seconds=value)
        object.__setattr__(self, name, effValue)


    def load(self, description, state={}):
        self.position = description['position']
        self.greenDuration = description['green']
        self.redDuration = description['red']
        # Load color from description if available.
        if 'state' in description: self.state = description['state']
        if 'id' in description: self.id = description['id']

        # Load current state of light.
        if 'state' in state: self.state = state['state']
        if 'lastSwitchTime' in state:
            self.lastSwitchTime = kts46.utils.str2timedelta(state['lastSwitchTime'])
