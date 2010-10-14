class Road:

    def __init__(self, length=1000, width=10, linesCount=1):
        self._length = length
        self._width = width
        self._linesCount = linesCount

    def get_length(self): return self._length
    def get_width(self): return self._width
    def get_lines_count(self): return self._linesCount
