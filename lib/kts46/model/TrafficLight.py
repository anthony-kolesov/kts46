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


import yaml
from datetime import timedelta
from uuid import uuid4

class SimpleSemaphore(yaml.YAMLObject):
    """Simple semaphore that works in one direction.

    Duration of green and red lights states are setted separatly.
    They are stored as datetime.timedelta type, but you can just a number, it
    will be used as a number of seconds in conversion. Id is always converted to
    unicode.
    """

    yaml_tag = u"!semaphore"
    yaml_loader = yaml.SafeLoader
    __green_state = "g"
    __red_state = "r"

    def __init__(self, id=None, position=0, greenDuration=5, redDuration=5):
        """Creates a new simple semaphore."""
        self.id = id if (id is not None) else uuid4()
        self.position = position
        self._last_switch_time = timedelta()
        self._state = SimpleSemaphore.__red_state
        self.greenDuration = 5
        self.redDuration = 5

    def switch(self, currentTime):
        "Switches semaphore to the other state and records current time."
        if self._state == SimpleSemaphore.__green_state:
            self._state = SimpleSemaphore.__red_state
        else:
            self._state = SimpleSemaphore.__green_state
        self._last_switch_time = currentTime

    def get_position(self): return self.position
    def get_state(self): return self._state
    def is_green(self): return self._state == SimpleSemaphore.__green_state
    def get_last_switch_time(self): return self._last_switch_time
    def get_id(self): return self.id

    def getNextSwitchTime(self):
        if self.is_green():
            addTime = self.greenDuration
        else:
            addTime = self.redDuration
        return self.get_last_switch_time() + addTime

    def get_description_data(self):
        return {'id': self.get_id(),
                'position': self.get_position()
        }

    def get_state_data(self):
        return {'state': self.get_state()}

    # Little metaprogramming magic, so it is possible to set duration as float
    # (in seconds). Also store in unicode explicitly.
    def __setattr__(self, name, value):
        effValue = value
        if name == "id" and value is not str:
            effValue = str(value)
        elif (name == "greenDuration" or name == "redDuration") and\
                not isinstance(value, timedelta):
            effValue = timedelta(seconds=value)
        yaml.YAMLObject.__setattr__(self, name, effValue)

    @classmethod
    def from_yaml(cls, loader, node):
        data = loader.construct_mapping(node)
        a = SimpleSemaphore()
        for attrName, attrValue in data.iteritems():
            a.__setattr__(attrName, attrValue)
        return a
