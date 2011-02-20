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
from kts46.model.Model import Model, ModelParams
from kts46.mongodb import StateStorage


def timedeltaToSeconds(td):
    return td.days * 24 * 60 * 60 + td.seconds + td.microseconds / 1000000.0


class SimulationServer(object):
    "A server object that does simulation of model."

    def __init__(self, cfg):
        self.cfg = cfg
        self.logger = logging.getLogger('kts46.SimulationServer')

    def runSimulationJob(self, job):
        """Runs simulation job.

        This function does all required stuff: gets initial state and definition,
        simulates and stores simulation results to database."""

        jobId = job.name

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
        batchLength = job.definition['simulationParameters']['batchLength']

        # Prepare infrastructure.
        saver = StateStorage(job, self.cfg.getint('worker', 'dbBatchLength'));
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
            #data['job'] = jobId
            # Round time to milliseconds
            t += step
            saver.add(round(t, 3), data)

        # Finalize.
        job.currentFullState = model.getStateData()
        job.db.progresses.update({'_id': job.id}, {'$inc': {'done': stepsCount}}, safe=True)
        saver.close()
        self.logger.debug('End time: {0}.'.format(t))
