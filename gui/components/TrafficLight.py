from datetime import timedelta

class SimpleSemaphore:
    "Simple semaphore that works in one direction."

    __green_state = "g"
    __red_state = "r"

    def __init__(self, interval=timedelta(seconds=5), position=0):
        """Creates a new simple semaphore.

        Interval must be time.timedelta. Position is measured in meters.
        """
        self._interval = interval
        self._position = position
        self._last_switch_time = timedelta()
        self._state = __red_state

    def switch(self, currentTime):
        self._state = __red_state if self._state == __green_state else __green_state
        self._last_switch_time = currentTime

    def get_position(self): return self._position
    def get_state(self): return self._state
    def is_green(self): return self._state == __green_state
    def get_last_switch_time(self): return self._last_switch_time
    def get_interval(self): return self._interval
