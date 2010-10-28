import logging, sqlite3, couchdb
from xpcom import components
from roadModel import Car, Road, SimpleSemaphore, Model

class MozConsoleHandler(logging.Handler):
    
    def __init__(self, level=logging.NOTSET):
        logging.Handler.__init__(self, level)
        self._log = self._log = components.classes['@mozilla.org/consoleservice;1'].getService(components.interfaces.nsIConsoleService)
        
    def emit(self, record):
        self._log.logStringMessage(record.getMessage())

class SQLiteStorage:

    def __init__(self, path):
        self.logger = logging.getLogger('roadModel.sqlitestorage')
        (self.conn, self.cur) = self.open(path)
        # DB schema
        self.cur.execute("DROP TABLE IF EXISTS states;")
        self.cur.execute("CREATE TABLE states (time float, state text);")
        self.dump() # Fix changes to scheme and start transaction.  
        
    def open(self, path):
        try:
            conn = sqlite3.connect(path)
        except sqlite3.OperationalError:
            self.logger.error("Couldn't open database file: %s." % path)
            raise
        cur = self.conn.cursor()
        return (conn, cur)
        
    def add(self, time, data):
        self.cur.execute('INSERT INTO states VALUES(:time, :state);',
                {'time': time, 'state': data} )
    
    def dump(self)
        self.conn.commit() # Dump previous transaction.
        self.cur.execute('BEGIN TRANSACTION;') # And begin new.
    
    def close(self):
        self.conn.commit() # Close TX.
        self.conn.close()


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
        # Prepare values.
        stepAsMs = step * 1000 # step in milliseconds
        stepsN = duration / step
        stepsCount = 0
        t = 0.0
        
        # Prepare infrastructure.
        logger = logging.getLogger('roadModel.manager')
        try:
            conn = sqlite3.connect(outpath)
        except sqlite3.OperationalError:
            logger.error("Couldn't open database file: %s." % outpath)
            return
        cur = conn.cursor()
        # DB schema
        cur.execute("DROP TABLE IF EXISTS states;")
        cur.execute("CREATE TABLE states (float time, string state);")
        conn.commit()
        logger.info('stepsN: %i, stepsCount: %i, stepsN/100: %i', stepsN, stepsCount, stepsN / 100)
        
        # Run.
        while t < duration:
            self.run_step(stepAsMs)
            stepsCount += 1
            if stepsCount % (stepsN / 100) == 0:
                reporter.report(t, duration)
                conn.commit()
                cur.execute('BEGIN TRANSACTION;')
            cur.execute('INSERT INTO states VALUES(:time, :state);',
                {'time': t, 'state': self.get_state_data()} )
            t += step
            
        # Finilize.
        reporter.report(1.0, 1.0) # Report exactly 100%
        conn.commit()
        conn.close()
        
# Add XPCOM log handler.
# Set up logging to file. Logging to XULRunner console will initialized automatically.
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m/%d %H:%M:%S',
                    filename='/tmp/rns-xul-runner.log',
                    filemode='w')
logging.getLogger('').addHandler(MozConsoleHandler())

