#!/usr/bin/env python

import csv
import sys
import tarfile
import yaml
import time
import random
import math
from pymw import pymw
from pymw import interfaces
from optparse import OptionParser
#import boinc

# Project imports
#PROJECT_LIB_PATH = '/home/anthony/kts46.boinc/lib/'
#if PROJECT_LIB_PATH not in sys.path:
#    sys.path.append(PROJECT_LIB_PATH)
#import kts46
import kts46.simulationServer
import kts46.offline_support

def configureCmdOptions():
    usage = "usage: %prog [options] modelFile.yaml"
    cmdOpts = OptionParser(usage=usage)

    cmdOpts.add_option('-s', '--states', action='store', dest='statesFile',
        default='states.csv',
        help="Output file for states." )
    cmdOpts.add_option('-v', '--cars', action='store', dest='carsFile',
        default='cars.csv',
        help="Output file for cars." )

    return interfaces.parse_options(cmdOpts)


def runTask(definition):
    ss = kts46.simulationServer.SimulationServer()
    storage = kts46.offline_support.MemoryStateStorage(definition['simulationParameters']['batchLength'])
    job = kts46.offline_support.OfflineJob(definition)
    ss.runSimulationJob(job, storage)
    return storage

        

options, args = configureCmdOptions()
inputFilePath = args[0]
statesFilePath = options.statesFile
carsFilePath = options.carsFile

with open(inputFilePath) as f:
    definition = yaml.load(f.read())

    
# get an interface object based on command-line options 
interface_obj = interfaces.get_interface(options)
if hasattr(interface_obj, "set_boinc_args"):
    interface_obj.set_boinc_args(1, 1, int(1e6))

pymw_master = pymw.PyMW_Master(interface=interface_obj)

tasks = [pymw_master.submit_task(runTask,
                                input_data=(definition, ),
                                modules=("kts46.simulationServer","kts46.offline_support", "yaml","jsonRpcClient"),
                                dep_funcs=())]

                                
res_task, result = pymw_master.get_result()

# Write result.
statesFile = open(statesFilePath, "wb")
carsFile = open(carsFilePath, "wb")

statesWriter = csv.writer(statesFile, quoting=csv.QUOTE_MINIMAL)
carsWriter = csv.writer(carsFile, quoting=csv.QUOTE_MINIMAL)
statesWriter.writerow( ["Time", "TimeAsTD",
    "Last car generation time", "Last car id"] )
carsWriter.writerow(["Time", "Car id", "Desired speed",
    "Current speed", "Position", "Line" ])

for car in result.cars:
    carsWriter.writerow(car)
for state in result.states:
    statesWriter.writerow(state)
    
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

print("Task has been done!")
