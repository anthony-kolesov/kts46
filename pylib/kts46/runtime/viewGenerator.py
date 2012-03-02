#!/usr/bin/python

import json
import sys
import yaml
from optparse import OptionParser
from kts46.model.Model import Model

def configureCmdOptions():
    cmdOpts = OptionParser()
    cmdOpts.add_option('-m', '--model', action='store', dest='model')
    cmdOpts.add_option('-c', '--cars', action='store', dest='cars', default=None)
    return cmdOpts.parse_args(sys.argv[1:])

def getPoint(model, pointName):
    if pointName in model['endpoints']:
        return model['endpoints'][pointName]
    return model['crossroads'][pointName]

options = configureCmdOptions()[0]

# Read input
with open(options.model) as f:
    model = Model(Model.defaultParams)
    model.load(yaml.load(f.read()))
if options.cars is not None:
    with open(options.cars) as f:
        cars = json.loads(f.read())
else:
    cars = {}

roads = {}
result = {
    'view': {'roads': roads},
    'viewParameters': model.view
}
for roadId, road in model.roads.iteritems():
    roads[roadId] = {
        'x1': road.points[0].coords['x'],
        'y1': road.points[0].coords['y'],
        'x2': road.points[1].coords['x'],
        'y2': road.points[1].coords['y'],
        'width': road.width
    }
    
result['cars'] = cars
result['viewParameters']['frameRate'] = 1.0 / model.simulationParameters['stepDuration']
    
print(json.dumps(result, indent=2))

