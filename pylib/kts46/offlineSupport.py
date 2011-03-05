class OfflineJob(object):

    def __init__(self, definition):
        self.currentFullState = None
        self.definition = definition
        self.progress = {}

    def saveSimulationProgress(self, stepsDone):
        pass

class MemoryStateStorage(object):

    def __init__(self, totalSteps):
        self.totalSteps = totalSteps
        self.stepsDone = 0
        self.cars = []
        self.states = []

    def add(self, time, data):

        # time as seconds, time as dt, lastCarGenerationTime
        state = [
            time,
            data['time'],
            data['lastCarGenerationTime'],
            data['lastCarId']
        ]
        self.states.append(state)

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
            self.cars.append(row)

        self.stepsDone += 1
        #boinc.set_fraction_done((float(self.stepsDone) / self.totalSteps) )

    def close(self):
        pass

    def repair(self, currentTime):
        pass
