#!/usr/bin/python

# Copyright 2010-2011 Anthony Kolesov
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
import glob
import json
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
        default='states.csv',
        help="Output file for states." )
    cmdOpts.add_option('--cars-file', action='store', dest='carsFile',
        default='cars.csv',
        help="Output file for cars." )
    cmdOpts.add_option('-o', '--out', action='store', dest='output',
        default='./',
        help="Directory to place output files. By default this is current working directory." )

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
            print('%g%%...' % (self.stepsDone * 100 / self.totalSteps))

    def close(self):
        pass

    def repair(self, currentTime):
        pass


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
    statesFile = open(statesFilePath, "wb")
    carsFile = open(carsFilePath, "wb")
    storage = CSVStateStorage(statesFile, carsFile, definition['simulationParameters']['batchLength'])
    job = OfflineJob(definition)
    ss.runSimulationJob(job, storage)

    # Close files for writing and reopen for reading.
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
