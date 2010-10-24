# from xpcom import components
#import yaml
import Car, Road, TrafficLight

__version__ = '0.1.2'

# Create aliases.
Car = Car.Car
Road = Road.Road
SimpleSemaphore = TrafficLight.SimpleSemaphore


# def road_constructor(loader, node):
#    mapping = loader.construct_mapping(node)
#    length = mapping
#    
#    value = loader.construct_scalar(node)
#    a, b = map(int, value.split('d'))
#    return Dice(a, b)
#
# yaml.add_constructor(u'!road', road_constructor)
