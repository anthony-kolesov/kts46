#!/usr/bin/python
import logging, couchdb, logging.handlers, sys, yaml, math
from SimpleXMLRPCServer import SimpleXMLRPCServer
from ConfigParser import SafeConfigParser
import CouchDBViewDefinitions

sys.path.append('../lib/')
from kts46 import Car, Road, SimpleSemaphore, Model, CouchDBStorage

def init():
    configFiles = ('rpc_server.ini', '../config/common.ini')

    """Initializes server infrastructure. Returns (SafeConfigParser, logger)."""
    # Create configuration.
    logging.debug('Reading configuration.')
    cfg = SafeConfigParser()
    cfg.read(configFiles)

    # Configure logging.
    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m/%d %H:%M:%S',
                    filename='/tmp/kts46_rpc_server.log',
                    filemode='w')

    # Define a log handler for rotating files.
    rfhandler = logging.handlers.RotatingFileHandler(cfg.get('log', 'filename'),
        maxBytes=cfg.get('log', 'maxBytesInFile'),
        backupCount=cfg.get('log', 'backupCountOfFile'))
    rfhandler.setLevel(logging.INFO)
    logging.getLogger('').addHandler(rfhandler)

    logger = logging.getLogger('kts46.rpc_server')

    return (cfg, logger)


def hello(msg):
    "Test method to check that server is working fine."
    return '''Hello you too! This is simple XML-RPC server for kts46.
            You\'ve said: [''' + msg + ']'

class ModelParams:
    
    def __init__(self):
        self.carGenerationInterval = 3.0
        self.safeDistance = 5.0
        self.maxSpeed = 20.0
        self.minSpeed = 10.0


class RPCServerException(Exception):
    pass


class CouchDBProxy:

    jobsCountDocId = 'jobsCount'
    lastId = 'lastId'
    jobProgressDocId = '%sProgress'

    def __init__(self, cfg):
        self.cfg = cfg
        self.logger = logging.getLogger('kts46.rpc_server.couchdb')
        self.server = couchdb.Server(cfg.get('couchdb', 'dbaddress'))

    def _createViews(self, projectName):
        "Creates all requires views for the database."

        defsStr = CouchDBViewDefinitions.definitions
        defs = [ ]
        for defStr in defsStr:
            defs.append(couchdb.design.ViewDefinition(defStr['doc'],
                defStr['view'], defStr['map']))
        couchdb.design.ViewDefinition.sync_many(self.server[projectName], defs )

    def getNewJobId(self, projectName):
        if projectName not in self.server:
            raise RPCServerException("Couldn't get new job id because project doesn't exist.")
        project = self.server[projectName]
        countDoc = project[CouchDBProxy.jobsCountDocId]
        countDoc[CouchDBProxy.lastId] = countDoc[CouchDBProxy.lastId] + 1
        project[CouchDBProxy.jobsCountDocId] = countDoc
        return countDoc[CouchDBProxy.lastId]
                

    def createProject(self, projectName):
        """Create in database project with specified name.
        
        An exception will be raised it project already exists.
        Arguments:
            projectName -- name of peoject to create."""
        if projectName not in self.server:
            project = self.server.create(projectName)
            # Create special document to store amount of jobs created.
            project[CouchDBProxy.jobsCountDocId] = {'lastId' : 0}
            self._createViews(projectName)
        else:
            msg = "Couldn't create project because it already exists."
            msg += ' Project name: %s.' % projectName
            raise RPCServerException(msg)


    def projectExists(self, projectName):
        "Checks whether project with specified name already exists."
        return projectName in self.server


    def deleteProject(self, projectName):
        """Deletes project with specified name if it exists. Otherwise raises
        RPCServerException."""
        if projectName in self.server:
            self.logger.debug("Deleting project '%s'." % projectName)
            del self.server[projectName]
            self.logger.info("Project '%s' deleted." % projectName)
        else:
            msg = "Couldn't delete project '%s' because it doesn't exists." % projectName
            self.logger.warning(msg)
            raise RPCServerException(msg)

            
    def addJob(self, projectName, jobName, definition):
        """Adds specified job to project.
        
        RPCServerException will be raised if project doesn't exist or job with
        specified name already exists.
        Arguments:
            projectName -- name of model project.
            jobName -- job name.
            definition -- definition of job written in YAML.
        """
        if projectName not in self.server:
            raise RPCServerException("""Couldn't add job '%s', because project
            '%s' doesn't exist.""" % (jobName, projectName))
        db = self.server[projectName]
        
        # Store simulation parameters.
        objData = yaml.safe_load(definition)
        simulationTime = objData['simulationTime']
        simulationStep = objData['simulationStep']
        
        jobId = 'j' + str(self.getNewJobId(projectName))
        db[jobId] = {'name': jobName, 'yaml': definition, 'type': 'job',
            'simulationTime': simulationTime, 'simulationStep': simulationStep}
        db[CouchDBProxy.jobProgressDocId % jobId] = {'job': jobId, 
            'totalSteps': math.floor(simulationTime/simulationStep),
            'done': 0 }
        

    #def modelExists(self, modelName):
    #    "Checks whether model with provided name already exists."
    #    return modelName in self.server
    
    #def deleteModel(self, modelName):
    #    "Deletes model with specified name if it exists. Otherwise creates an exception."
    #    if modelName in self.server:
    #        self.logger.info("Deleting model with name '%s'." % modelName)
    #        del self.server[modelName]
    #    else:
    #        raise Exception("""Couldn't delete model with name '%s' because it
    #                         doesn't exists.""" % modelName)
            
    def simulate(self, projectName, jobId):
        """Simulates model for the specified time duration.
        
        modelName - name of model to simulate.
        duration - duration of simulation in seconds.
        step - step of simulation in seconds.
        """

        # Prepare infrastructure.
        logger = logging.getLogger('kts46.rpc_server.simulator')
        storage = CouchDBStorage(self.cfg.get('couchdb', 'dbaddress'), projectName, jobId)

        model = Model(ModelParams())
        job = self.server[projectName]['j'+jobId]
        model.loadYAML(job['yaml'])
        step = job['simulationStep']
        duration = job['simulationTime']
        
        # Prepare values.
        stepAsMs = step * 1000 # step in milliseconds
        stepsN = duration / step
        stepsCount = 0
        t = 0.0
        logger.info('stepsN: %i, stepsCount: %i, stepsN/100: %i', stepsN, stepsCount, stepsN / 100)

        # Run.
        while t < duration:
            model.run_step(stepAsMs)
            stepsCount += 1
            # Round time to milliseconds
            storage.add(round(t, 3),  model.get_state_data())
            t += step

        # Finilize.
        storage.close()
            
if __name__ == '__main__':
    cfg, logger = init()

    # Create and configure server.
    address = cfg.get('connection', 'address')
    port = cfg.getint('connection', 'port')
    server = SimpleXMLRPCServer( (address, port), allow_none = True )

    # Register functions.
    couchdbProxy = CouchDBProxy(cfg)
    server.register_function(hello)
    server.register_instance(couchdbProxy)

    # Run server.
    logging.warn('Serving...')
    server.serve_forever()
