from uuid import uuid4

class Car:

    def __init__(self, id=None, speed=15, length=4.5, width=1.5, position=0,
                linePosition=0):
        """Initializes a new car object.

        Creates new car using given parameters. Speed is measured in m/s, length,
        width and position in metres.
        """
        if id is None:
            self._id = unicode(uuid4())
        else:
            self._id = unicode(id)
        self._speed = speed
        self._length = length
        self._width = width
        self._position = position
        self.linePosition = linePosition

    def move(self, distance):
        "Moves car on specified distance forward."
        if distance < 0:
            raise Exception("Distance of car moving can't be negative. " +
                            "Backword moving isn't currently allowed.")
        self._position += distance

    def get_speed(self): return self._speed
    def get_length(self): return self._length
    def get_width(self): return self._width
    def get_position(self): return self._position
    def get_id(self): return self._id

    def get_description_data(self):
        return {'id': self.get_id(),
                'length': self.get_length(),
                'width': self.get_width()
        }

    def get_state_data(self):
        return {'position': self.get_position(),
                'line': self.linePosition
        }
