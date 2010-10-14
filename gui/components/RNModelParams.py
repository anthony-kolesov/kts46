from xpcom import components, verbose

class RNModelParams:
    _com_interfaces_ = components.interfaces.nsIRNModelParams
    _reg_clsid_ = "{ec4dc070-620c-4339-8a2b-8d3eb8911684}"
    _reg_contractid_ = "@kolesov.blogspot.com/RoadNetworkModelParams;1"

    def __init__(self):
        self.carGenerationInterval = 3.0
