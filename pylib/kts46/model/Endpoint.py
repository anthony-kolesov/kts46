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

from datetime import timedelta

class Endpoint(object):
    "Defines an endpoint where cars come in and come out of model."

    def __init__(self, name, coords, inputRate):
        "Creates new endpoint."
        self.name = name
        self.coords = coords
        self.inputRate = inputRate
        self.enterQueue = []
        self.lastGenerationTime = timedelta(0)
        self.road = None 


    def getDescriptionData(self):
        "Gets dictionary with parameters of endpoint."
        return {
                    'name': self.name,
                    'enterQueueLength' : len(self.enterQueue)
               }

