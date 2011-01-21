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

import logging
import yaml
from uuid import uuid4

class Car(yaml.YAMLObject):

    yaml_tag = u"!car"
    yaml_loader = yaml.SafeLoader

    INACTIVE = 'inactive'
    ADDED = 'add'
    ACTIVE = 'active'
    DEFAULT = 'active'
    DELETED = 'del'

    def __init__(self, id=None, speed=15, length=4.5, width=1.5, position=0,
                line=0):
        """Initializes a new car object.

        Creates new car using given parameters. Speed is measured in m/s, length,
        width and position in metrs.
        """
        if id is None:
            self._id = str(uuid4())
        else:
            self._id = str(id)
        self._speed = speed
        self._length = length
        self._width = width
        self._position = position
        self.line = line
        self.state = Car.INACTIVE

    def move(self, distance):
        "Moves car on specified distance forward. Distance couldn't be negative."
        if distance < 0:
            msg = "Distance of car moving can't be negative. " + \
                "Backwards moving isn't currently allowed."
            logging.getLogger('roadModel').error(msg)
            raise Exception(msg)
        self._position += distance

    def get_speed(self): return self._speed
    def get_length(self): return self._length
    def get_width(self): return self._width
    def get_position(self): return self._position
    def get_id(self): return self._id

    def get_description_data(self):
        return {'id': self.get_id(),
                'length': self.get_length(),
                'width': self.get_width(),
                'line': self.line
        }

    def get_state_data(self):
        d = {'pos': round(self.get_position(), 2),
             'line': self.line
        }
        if self.state != Car.DEFAULT:
            d['state'] = self.state
        return d
