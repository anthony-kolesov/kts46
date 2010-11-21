#!/usr/bin/python
import json, pprint, sys
import numpy
from urllib2 import urlopen
from string import Template
from ConfigParser import SafeConfigParser

configFiles = ('../config/common.ini',)

def getJSON(url):
    a = urlopen(url)
    text = a.read(None).decode("UTF-8", "strict")
    a.close()
    return json.loads(text)

# Read configuration file.
cfg = SafeConfigParser()
cfg.read(configFiles)

# Parse cmd arsg.
dbName = sys.argv[1]

dbPath = Template(cfg.get("couchdb", "basicStatsDbPath")).safe_substitute(dbname=dbName)

# Connect to CouchDB and get data.
addCarData = getJSON(dbPath + cfg.get("couchdb", "addCarView"))
delCarData = getJSON(dbPath + cfg.get("couchdb", "deleteCarView"))

addCarTimes = dict( (x['key'], x['value']['time']) for x in addCarData['rows'])
delCarTimes = dict( (x['key'], x['value']['time']) for x in delCarData['rows'])

times = {}
moveTimes = []
for carid, addTime in addCarTimes.items():
    if carid in delCarTimes:
        times[carid] = {'add': addTime, 'del': delCarTimes[carid]}
        moveTimes.append(delCarTimes[carid] - addTime)

# Create numpy array and count statistics.
arr = numpy.array(moveTimes)
print("Average: %f" % numpy.average(arr) )
# print("Mean: %f" % numpy.mean(arr) )
print("Standard deviation: %f" % numpy.std(arr) )
