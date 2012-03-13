# Copyright 2010-2012 Anthony Kolesov
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

class Crossroad(object):
    "Defines an endpoint where cars come in and come out of model."

    def __init__(self, name, coords, trafficLight=None):
        "Creates new endpoint."
        self.name = name
        self.coords = coords
        self.roads = [None, None, None, None]
        self.directions = [None, None, None, None]
        self.trafficLight = trafficLight


    def getDescriptionData(self):
        return {'name': self.name}
