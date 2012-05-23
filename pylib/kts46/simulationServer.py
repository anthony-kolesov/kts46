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


import logging
from kts46.model.Model import Model


def timedeltaToSeconds(td):
    return td.days * 24 * 60 * 60 + td.seconds + td.microseconds / 1000000.0


class SimulationServer(object):
    "A server object that does simulation of model."

    def __init__(self, cfg=None):
        self.logger = logging.getLogger('kts46.SimulationServer')

    def runSimulationJob(self, job, saver, ignore_batch=False):
        """Runs simulation job.

        This function does all required stuff: gets initial state and definition,
        simulates and stores simulation results to database."""

        model = Model(Model.defaultParams)

        # Load current state: load state and set time
        curState = job.currentFullState
        if curState is not None:
            model.load(job.definition, curState)
            t = timedeltaToSeconds(model.time)
        else:
            model.load(job.definition)
            t = 0.0

        step = job.definition['simulationParameters']['stepDuration']
        duration = job.definition['simulationParameters']['duration']
        if ignore_batch:
            batchLength = int(duration / step)
        else:
            batchLength = job.definition['simulationParameters']['batchLength']

        # Prepare infrastructure.
        saver.repair(t)

        # Reset job progress step counter.
        if t == 0.0:
            # Document will be saved to database with state data.
            job.progress['done'] = 0

        # Prepare values.
        stepAsMs = step * 1000 # step in milliseconds
        stepsN = duration / step
        stepsCount = 0

        # if is start then save it as initial state.
        if t == 0.0:
            saver.add(round(t, 3), data = model.getStateData())

        # Run.
        while t <= duration and stepsCount < batchLength:
            model.run_step(stepAsMs)
            stepsCount += 1
            data = model.getStateData()
            t += step
            saver.add(round(t, 3), data)

        # Finalize.
        job.currentFullState = model.getStateData()
        job.saveSimulationProgress(stepsCount)
        saver.close()
        self.logger.debug('End time: {0}.'.format(t))

        logging.info('InputRate: {0}, crossroad: {1}'.format(model.params['inputRate'], model.crossroads.values()[0].trafficLight))
        for p in model.endpoints.itervalues():
            logging.info('Name: {0}, entered: {1}, exited: {2}, left in enterQueue {3}.'.format(p.name, p.entered, p.exited, len(p.enterQueue)))
        #cnt = 0
        #sum_time = datetime.datetime()
        #for t in model.move_times:
        #    sum_time += t
        import numpy
        times_array = numpy.array(model.move_times)
        logging.info('Average moveTime: {0}, stdev: {1}.'.format(numpy.average(times_array), numpy.std(times_array)))

