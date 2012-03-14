#!/usr/bin/python

import json
import sys
import yaml
from optparse import OptionParser
from kts46.model.Model import Model
from kts46.model.Car import Car

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
resultCars = []
result = {
    'view': {'roads': roads},
    'viewParameters': model.view,
    'cars': resultCars
}
result['viewParameters']['frameRate'] = 1.0 / model.simulationParameters['stepDuration']

for roadId, road in model.roads.iteritems():
    roads[roadId] = {
        'x1': road.points[0].coords['x'],
        'y1': road.points[0].coords['y'],
        'x2': road.points[1].coords['x'],
        'y2': road.points[1].coords['y'],
        'width': road.width
    }

for timeCars in cars:
    a = []
    resultCars.append(a)
    for car in timeCars:
        roadId = car['road']
        del car['road']
        carObj = Car(model, model.roads[roadId])
        carObj.load(car)
        road = carObj.road
        
        relativePosition = float(carObj.position) / road.length
        point0 = road.getFirstEndpoint(carObj.direction)[0]
        point1 = road.getNextEndpoint(carObj.direction)[0]

        if road.isHorizontalRoad():
            xcoor = 'x'
            ycoor = 'y'
        else:
            xcoor = 'y'
            ycoor = 'x'
        
        lineWidth = float(road.width) / sum(road.lines)
        carX = (point1.coords[xcoor] - point0.coords[xcoor]) * relativePosition + point0.coords[xcoor]
        yOffset = lineWidth * (road.lines[carObj.direction] - carObj.line - 1)
        if point0.coords[xcoor] > point1.coords[xcoor]:
            yOffset = (-yOffset) - carObj.width
        carY = ( (point1.coords[ycoor] - point0.coords[ycoor]) * relativePosition
                 + point0.coords[ycoor] + yOffset)
        if not road.isHorizontalRoad():
            carX, carY = (carY, carX)
            carObj.length, carObj.width = (carObj.width, carObj.length)

        newData = {'l': carObj.length, 'w': carObj.width, 'p': (carX, carY)}
        
        a.append(newData)

print(json.dumps(result))
