# from xpcom import components
import logging
import Car as CarModule, Road as RoadModule, TrafficLight as TrafficLightModule,\
    Model as ModelModule

__version__ = '0.1.2'

# Create aliases.
Car = CarModule.Car
Road = RoadModule.Road
SimpleSemaphore = TrafficLightModule.SimpleSemaphore
Model = ModelModule.Model

# def road_constructor(loader, node):
#    mapping = loader.construct_mapping(node)
#    length = mapping
#    
#    value = loader.construct_scalar(node)
#    a, b = map(int, value.split('d'))
#    return Dice(a, b)
#
# yaml.add_constructor(u'!road', road_constructor)
