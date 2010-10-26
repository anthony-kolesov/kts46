import logging
from xpcom import components
from roadModel import Car, Road, SimpleSemaphore, Model

class MozConsoleHandler(logging.Handler):
    
    def __init__(self, level=logging.NOTSET):
        logging.Handler.__init__(self, level)
        self._log = self._log = components.classes['@mozilla.org/consoleservice;1'].getService(components.interfaces.nsIConsoleService)
        
    def emit(self, record):
        self._log.logStringMessage(record.getMessage())



class RoadNetworkModel:
    _com_interfaces_ = components.interfaces.nsIRoadNetworkModel
    _reg_clsid_ = "{efabba84-e20e-46b6-98bb-ef67fc0ab496}"
    _reg_contractid_ = "@kolesov.blogspot.com/RoadNetworkModel;1"

    def __init__(self):
        self.params = components\
            .classes["@kolesov.blogspot.com/RoadNetworkModelParams;1"]\
            .createInstance()
        self._log = components.classes['@mozilla.org/consoleservice;1'].getService(components.interfaces.nsIConsoleService)
        self._model = Model(self.params)

    def run_step(self, milliseconds):
        self._model.run_step(milliseconds)
        
    def get_state_data(self):
        return self._model.get_state_data()

    def get_description_data(self):
        return self._model.get_description_data()

    def loadYAML(self, yamlData):
        self._model.loadYAML(yamlData)

    def simulate(self, duration, step, outpath, reporter):
        stepAsMs = step * 1000 # step in milliseconds
        stepsN = duration / step
        stepsCount = 0
        t = 0.0
        logger = logging.getLogger("")
        while t < duration:
            self.run_step(stepAsMs)
            stepsCount += 1
            if stepsN % stepsCount == 0:
                reporter.report(t, duration)
            t += step
        reporter.report(1.0, 1.0) # Report exactly 100%
        
# Add XPCOM log handler.
# Set up logging to file. Logging to XULRunner console will initialized automatically.
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m/%d %H:%M:%S',
                    filename='/tmp/rns-xul-runner.log',
                    filemode='w')
logging.getLogger('').addHandler(MozConsoleHandler())
logging.info("HAHA")
