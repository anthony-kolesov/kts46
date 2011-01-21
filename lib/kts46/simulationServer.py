"""
License:
   Copyright 2010-2011 Anthony Kolesov

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import logging
from kts46.model.Model import Model
from kts46.modelParams import ModelParams
from kts46.mongodb import StateStorage


def timedeltaToSeconds(td):
    return td.days * 24 * 60 * 60 + td.seconds + td.microseconds / 1000000.0


class SimulationServer(object):
    "A server object that does simulation of model."

    def __init__(self):
        self.logger = logging.getLogger('kts46.SimulationServer')

    def runSimulationJob(self, job):
        """Runs simulation job.

        This function does all required stuff: gets initial state and definition,
        simulates and stores simulation results to database."""

        jobId = job.name

        model = Model(ModelParams())
        model.loadYAML(job.definition)
        step = job.simulationParameters['stepDuration']
        duration = job.simulationParameters['duration']
        batchLength = job.simulationParameters['batchLength']

        # Prepare infrastructure.
        #saver = CouchDBStateStorage(job, model.asYAML)
        saver = StateStorage(job, model.asYAML)

        # Load current state: load state and set time
        if len(job.progress['currentFullState']) > 0:
            model.loadYAML(job.progress['currentFullState'])
            t = timedeltaToSeconds(model.time)
        else:
            t = 0.0

        # Reset job progress step counter.
        if t == 0.0:
            # Document will be saved to database with state data.
            job.progress['done'] = 0

        # Prepare values.
        stepAsMs = step * 1000 # step in milliseconds
        stepsN = job.simulationParameters['duration'] / step
        stepsCount = 0
        self.logger.debug('Start time: {0}, step: {0}'.format(t, step))

        # Run.
        while t <= duration and stepsCount < batchLength:
            model.run_step(stepAsMs)
            stepsCount += 1
            data = model.get_state_data()
            data['job'] = jobId
            # Round time to milliseconds
            saver.add(round(t, 3), data)
            t += step

        # Finalize.
        saver.close()
        self.logger.debug('End time: {0}.'.format(t))

        #f1 = open('/tmp/kts46-state.txt', 'w')
        #f1.write(model.asYAML())
        #f1.close()
