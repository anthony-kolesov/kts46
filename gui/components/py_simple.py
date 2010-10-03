from xpcom import components, verbose

class PySimple: #PythonTestComponent
    _com_interfaces_ = components.interfaces.nsISimple
    _reg_clsid_ = "{c456ceb5-f142-40a8-becc-764911bc8ca5}"
    _reg_contractid_ = "@mozilla.org/PySimple;1"
    def __init__(self):
        self.yourName = "a default name" # or mName ?

    def __del__(self):
        if verbose:
            print "PySimple: __del__ method called - object is destructing"

    def write(self):
        print self.yourName

    def change(self, newName):
        self.yourName = newName