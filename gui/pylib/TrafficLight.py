from datetime import timedelta
from uuid import uuid4

class SimpleSemaphore:
    "Simple semaphore that works in one direction."

    __green_state = "g"
    __red_state = "r"

    def __init__(self, id=None, interval=timedelta(seconds=5), position=0):
        """Creates a new simple semaphore.

        Interval must be time.timedelta. Position is measured in meters.
        """
        if id is None:
            self._id = unicode(uuid4())
        else:
            self._id = unicode(id)
        self._interval = interval
        self._position = position
        self._last_switch_time = timedelta()
        self._state = SimpleSemaphore.__red_state

    def switch(self, currentTime):
        if self._state == SimpleSemaphore.__green_state:
            self._state = SimpleSemaphore.__red_state
        else:
            self._state = SimpleSemaphore.__green_state
        self._last_switch_time = currentTime

    def get_position(self): return self._position
    def get_state(self): return self._state
    def is_green(self): return self._state == SimpleSemaphore.__green_state
    def get_last_switch_time(self): return self._last_switch_time
    def get_interval(self): return self._interval
    def get_id(self): return self._id

    def get_description_data(self):
        return {'id': self.get_id(),
                'position': self.get_position()
        }

    def get_state_data(self):
        return {'state': self.get_state()}
