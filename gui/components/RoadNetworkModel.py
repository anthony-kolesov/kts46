from xpcom import components
from roadModel import Car, Road, SimpleSemaphore, Model

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
