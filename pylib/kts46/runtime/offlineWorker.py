#!/usr/bin/python

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

import atexit
import csv
import datetime
import glob
import json
import logging
import os
import os.path
import sys
import tarfile
import tempfile
import yaml
from ConfigParser import SafeConfigParser
from optparse import OptionParser

# Project imports
#PROJECT_LIB_PATH = '../../'
#if PROJECT_LIB_PATH not in sys.path:
#    sys.path.append(PROJECT_LIB_PATH)
from kts46.simulationServer import SimulationServer


def configureCmdOptions():
    usage = "usage: %prog [options] modelFile.yaml*"
    cmdOpts = OptionParser(usage=usage)

    cmdOpts.add_option('--states-file', action='store', dest='statesFile',
        default='states.js',
        help="Output file for states." )
    cmdOpts.add_option('--cars-file', action='store', dest='carsFile',
        default='cars.js',
        help="Output file for cars." )
    cmdOpts.add_option('-o', '--out', action='store', dest='output',
        default='./',
        help="Directory to place output files. By default this is current working directory." )
    cmdOpts.add_option('--no-out', action='store_true', dest='no_out', default=False)

    return cmdOpts.parse_args(sys.argv[1:])


class OfflineJob(object):

    def __init__(self, definition):
        self.currentFullState = None
        self.definition = definition
        self.progress = {}

    def saveSimulationProgress(self, stepsDone):
        pass

class CSVStateStorage(object):

    def __init__(self, statesFile, carsFile, totalSteps):
        self.totalSteps = totalSteps
        self.stepsDone = 0
        self.statesWriter = csv.writer(statesFile, quoting=csv.QUOTE_MINIMAL)
        self.carsWriter = csv.writer(carsFile, quoting=csv.QUOTE_MINIMAL)

        self.statesWriter.writerow( ["Time", "TimeAsTD",
            "Enter queue"] )
        self.carsWriter.writerow(["Time", "Car id", "Desired speed",
            "Current speed", "Position", "Line" ])


    def add(self, time, data):

        # time as seconds, time as dt, lastCarGenerationTime
        state = [
            time,
            data['time'],
            json.dumps(data['endpoints'])
        ]
        self.statesWriter.writerow(state)

        for carId, car in data['cars'].items():
            row = [
                time,
                carId,
                car['desiredSpeed'],
                car['curspd'],
                car['pos'],
                car['line'],
                car['width'],
                car['length']
            ]
            self.carsWriter.writerow(row)

        self.stepsDone += 1
        if ( self.stepsDone % 100 == 0) or (self.stepsDone == self.totalSteps):
            print('%4.0f%%...' % (self.stepsDone * 100 / self.totalSteps))

    def close(self):
        pass

    def repair(self, currentTime):
        pass


class EmptyStorage:
    def __init__(self, steps_total):
        self.steps_done = 0
        self.steps_total = steps_total
    def add(self, time, data):
        self.steps_done += 1
        if ( self.steps_done % (self.steps_total / 20) == 0):
            logging.info('%3.0f%%...' % (self.steps_done * 100.0 / self.steps_total))
    def close(self):
        pass
    def repair(self, currentTime):
        pass



class JSONStateStorage:
    
    def __init__(self, statesFile, carsFile, totalSteps):
        self.totalSteps = totalSteps
        self.stepsDone = 0
        self.states = []
        self.carsFile = carsFile
        self.cars = []
        self.trafficLights = {}
        self.trafficLightsInfo = {}

    def add(self, time, data):
        stateCars = []
        for carId, car in data['cars'].items():
            stateCars.append({
                'carId': carId,
                'pos': car['pos'],
                'line': car['line'],
                'width': car['width'],
                'length': car['length'],
                'road': car['road'],
                'dir': car['dir']
            })
        self.cars.append(stateCars)

        # Traffic lights
        addTl = False
        for tl in data['trafficLights']:
            addTl = False
            if tl['id'] in self.trafficLightsInfo:
                if tl['state'] != self.trafficLightsInfo[tl['id']]['state']:
                    addTl = True
            else:
                addTl = True
            
            if addTl:
                if self.stepsDone not in self.trafficLights:
                    self.trafficLights[self.stepsDone] = []
                self.trafficLights[self.stepsDone].append({'id': tl['id'], 'state': tl['state']})
                self.trafficLightsInfo[tl['id']] = tl

        self.stepsDone += 1
        if ( self.stepsDone % (self.totalSteps / 20) == 0):
            print('%3.0f%%...' % (self.stepsDone * 100.0 / self.totalSteps))

    def close(self):
        json.dump({'cars': self.cars, 'trafficLights': self.trafficLights}, self.carsFile)
        #json.dump({'trafficLights': self.trafficLights, 'cars': []}, self.carsFile, indent=2)

    def repair(self, currentTime):
        pass

logging.basicConfig(level=logging.INFO)
cfg = SafeConfigParser()
options, inputFilePaths = configureCmdOptions()

# Configure output directory.
if os.path.exists(options.output):
    if not os.path.isdir(options.output):
        raise Exception("Specified output directory isn't a directory at all.")
else:
    # Recursive creation: make all intermediate directories.
    os.makedirs(options.output)

# Temp data
#tempDir = tempfile.mkdtemp(prefix='kts46-')
#statesFilePath = os.path.join(tempDir, options.statesFile)
#carsFilePath = os.path.join(tempDir, options.carsFile)
statesFilePath = options.statesFile
carsFilePath = options.carsFile

# Remove temp directory
#atexit.register(lambda dir: os.rmdir(dir), tempDir)

for inputFilePath in inputFilePaths:
    # Get model definition
    with open(inputFilePath) as f:
        definition = yaml.load(f.read())

    # Simulate
    ss = SimulationServer(cfg)

    if options.no_out:
        storage = EmptyStorage(int(definition['simulationParameters']['duration'] / definition['simulationParameters']['stepDuration']))
    else:
        statesFile = open(statesFilePath, "wb")
        carsFile = open(carsFilePath, "wb")
        storage = JSONStateStorage(statesFile, carsFile,
            definition['simulationParameters']['duration'] / definition['simulationParameters']['stepDuration'])
    job = OfflineJob(definition)
    logging.info(datetime.datetime.now())
    ss.runSimulationJob(job, storage, ignore_batch=True)
    logging.info(datetime.datetime.now())

    # Close files for writing and reopen for reading.
    if not options.no_out:
        statesFile.close(), carsFile.close()
    #statesFile = open(statesFilePath, "rb")
    #carsFile = open(carsFilePath, "rb")

    # Compress
    #tarName = os.path.splitext(os.path.split(inputFilePath)[1])[0]
    #outpath = os.path.join(options.output, tarName + ".tar.bz2")
    #tar = tarfile.open(outpath, "w:bz2")
    #tar.add(statesFilePath, arcname=tarName+'/'+os.path.basename(statesFilePath))
    #tar.add(carsFilePath, arcname=tarName+'/'+os.path.basename(carsFilePath))

    # Cleanup
    #tar.close()
    #statesFile.close(), carsFile.close()
    #os.remove(statesFilePath), os.remove(carsFilePath)
