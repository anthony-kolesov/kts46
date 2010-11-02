#!/usr/bin/python
import json, pprint
import numpy
#from urllib.request import urlopen
from urllib2 import urlopen

def getJSON(url):
    a = urlopen(url)
    text = a.read(None).decode("UTF-8", "strict")
    a.close()
    return json.loads(text)

dbPath = "http://localhost:5984/rns_15/_design/basicStats/_view"

# Connect to CouchDB and get data.
addCarData = getJSON(dbPath + "/addCar")
delCarData = getJSON(dbPath + "/deleteCar")

addCarTimes = dict((x['key'], x['value']['time']) for x in addCarData['rows'])
delCarTimes = dict((x['key'], x['value']['time']) for x in delCarData['rows'])


times = {}
moveTimes = []
for carid, addTime in addCarTimes.items():
    if carid in delCarTimes:
        times[carid] = {'add': addTime, 'del': delCarTimes[carid]}
        moveTimes.append(delCarTimes[carid] - addTime)

# Create numpy array and count statistics.
arr = numpy.array(moveTimes)
print("Average: %f" % numpy.average(arr) )
print("Mean: %f" % numpy.mean(arr) )
print("Standard deviation: %f" % numpy.std(arr) )
