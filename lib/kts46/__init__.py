import CouchDBStorage as CouchDBStorageModule, Car as CarModule,\
    Road as RoadModule, TrafficLight as TrafficLightModule, Model as ModelModule

__version__ = '0.1.2'

# Create aliases.
CouchDBStorage = CouchDBStorageModule.CouchDBStorage
Car = CarModule.Car
Road = RoadModule.Road
SimpleSemaphore = TrafficLightModule.SimpleSemaphore
Model = ModelModule.Model

