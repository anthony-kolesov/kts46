from datetime import timedelta
from uuid import uuid4
import yaml

class SimpleSemaphore(yaml.YAMLObject):
    "Simple semaphore that works in one direction."
    
    yaml_tag = u"!semaphore"
    yaml_loader = yaml.SafeLoader
    __green_state = "g"
    __red_state = "r"

    def __init__(self, id=None, position=0):
        """Creates a new simple semaphore.

        Interval must be time.timedelta. Position is measured in meters.
        """
        if id is None:
            id = uuid4()
        self.id = id
        self.position = position
        self._last_switch_time = timedelta()
        self._state = SimpleSemaphore.__red_state
        self.greenDuration = 5
        self.redDuration = 5

    def switch(self, currentTime):
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
        
    def __setattr__(self, name, value):
        effValue = value
        if name == "id" and value is not unicode:
            effValue = unicode(value)
        elif (name == "greenDuration" or name == "redDuration") and value is not timedelta:
            effValue = timedelta(seconds=value)
        yaml.YAMLObject.__setattr__(self, name, effValue)
