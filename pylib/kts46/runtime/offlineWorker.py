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

import csv
import sys
import tarfile
import yaml
from ConfigParser import SafeConfigParser
from optparse import OptionParser

# Project imports
PROJECT_LIB_PATH = '../../'
if PROJECT_LIB_PATH not in sys.path:
    sys.path.append(PROJECT_LIB_PATH)
from kts46.simulationServer import SimulationServer


def configureCmdOptions():
    usage = "usage: %prog [options] modelFile.yaml"
    cmdOpts = OptionParser(usage=usage)

    cmdOpts.add_option('-s', '--states', action='store', dest='statesFile',
        default='states.csv',
        help="Output file for states." )
    cmdOpts.add_option('-c', '--cars', action='store', dest='carsFile',
        default='cars.csv',
        help="Output file for cars." )

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
            "Last car generation time", "Last car id"] )
        self.carsWriter.writerow(["Time", "Car id", "Desired speed",
            "Current speed", "Position", "Line" ])


    def add(self, time, data):

        # time as seconds, time as dt, lastCarGenerationTime
        state = [
            time,
            data['time'],
            data['lastCarGenerationTime'],
            data['lastCarId']
        ]
        self.statesWriter.writerow(state)

        for carId, car in data['cars'].items():
            row = [
                time,
                carId,
                car['desiredSpeed'],
                car['curspd'],
                car['pos'],
                car['line']#,
                #car['width'],
                #car['length']
            ]
            self.carsWriter.writerow(row)

        self.stepsDone += 1
        if (self.stepsDone % 100 == 0) or (self.stepsDone == self.totalSteps):
            with open("done.txt", "w") as f:
                f.write( str(float(self.stepsDone) / self.totalSteps) )

    def close(self):
        pass

    def repair(self, currentTime):
        pass

cfg = SafeConfigParser()
options, args = configureCmdOptions()
inputFilePath = args[0]
statesFilePath = options.statesFile
carsFilePath = options.carsFile

with open(inputFilePath) as f:
    definition = yaml.load(f.read())

ss = SimulationServer(cfg)
statesFile = open(statesFilePath, "wb")
carsFile = open(carsFilePath, "wb")

storage = CSVStateStorage(statesFile, carsFile, definition['simulationParameters']['batchLength'])
job = OfflineJob(definition)
ss.runSimulationJob(job, storage)

# Close files for writing
statesFile.close()
carsFile.close()

# Reopen file for reading
statesFile = open(statesFilePath, "rb")
carsFile = open(carsFilePath, "rb")

tar = tarfile.open("data.tar.bz2", "w:bz2")
tar.addfile(tar.gettarinfo(fileobj=statesFile), statesFile)
tar.addfile(tar.gettarinfo(fileobj=carsFile), carsFile)

tar.close()
statesFile.close()
carsFile.close()
