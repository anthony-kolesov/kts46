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

class Road(yaml.YAMLObject):
    "Defines a road in the model."

    yaml_tag = u"!road"
    yaml_loader = yaml.SafeLoader

    def __init__(self, length=1000, width=10, lines=1):
        "Creates new road."
        self.length = length
        self.width = width
        self.lines = lines

    def getDescriptionData(self):
        "Gets dictionary describing this road."
        return {'length': self.length,
                'width': self.width,
                'lines': self.lines
               }
