"""
License:
   Copyright 2010 Anthony Kolesov

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import CouchDBStorage as CouchDBStorageModule, Car as CarModule,\
    Road as RoadModule, TrafficLight as TrafficLightModule, Model as ModelModule

__version__ = '0.1.2'

# Create aliases.
CouchDBStorage = CouchDBStorageModule.CouchDBStorage
Car = CarModule.Car
Road = RoadModule.Road
SimpleSemaphore = TrafficLightModule.SimpleSemaphore
Model = ModelModule.Model

