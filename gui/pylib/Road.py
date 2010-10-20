import yaml

class Road(yaml.YAMLObject):
    yaml_tag = u"!road"
    yaml_loader = yaml.SafeLoader

    def __init__(self, length=1000, width=10, linesCount=1):
        self.length = length
        self.width = width
        self.linesCount = linesCount

    def get_length(self): return self.length
    def get_width(self): return self.width
    def get_lines_count(self): return self.linesCount
