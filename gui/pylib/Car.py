class Car:

    def __init__(self, speed=15, length=4.5, width=1.5, position=0):
        """Initializes a new car object.
        
        Creates new car using given parameters. Speed is measured in m/s, length,
        width and position in metres.
        """
        self._speed = speed
        self._length = length
        self._width = width
        self._position = position
    
    def move(self, distance):
        "Moves car on specified distance forward."
        if diatnce < 0:
            raise Exception("Distance of car moving can't be negative. " +
                            "Backword moving isn't currently allowed.")
        self._position += distance

    def get_speed(self): return self._speed
    def get_length(self): return self._length
    def get_width(self): return self._width
    def get_position(self): return self._position
