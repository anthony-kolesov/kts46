import unittest, xmlrpclib, couchdb
from ConfigParser import SafeConfigParser

class Test(unittest.TestCase):

    def setUp(self):
        configFiles = ('rpc_client.ini', '../stats/basicStats.ini')
    
        self.cfg = SafeConfigParser()
        self.cfg.read(configFiles)
        host = self.cfg.get('connection', 'server')
        port = self.cfg.getint('connection', 'port')
        connString = 'http://%s:%i' % (host, port)
        self.sp = xmlrpclib.ServerProxy(connString)
        self.projName = 'test_project_abracadabra'


    def test_projectExists(self):
        self.assertFalse( self.sp.projectExists(self.projName) )
        
        
    def test_createAndDeleteProject(self):
        self.assertFalse( self.sp.projectExists(self.projName) )
        self.sp.createProject(self.projName)
        self.assertTrue( self.sp.projectExists(self.projName) )
        self.sp.deleteProject(self.projName)
        self.assertFalse( self.sp.projectExists(self.projName) )
        
    def test_createViews(self):
        if self.sp.projectExists(self.projName):
            self.sp.createProject(self.projName)
        self.assertFalse( self.sp.projectExists(self.projName) )
        self.sp.createProject(self.projName)
        
        server = couchdb.Server(self.cfg.get('couchdb', 'dbaddress'))
        db = server[self.projName]
        self.assertTrue('_design/manage' in db)
        self.assertTrue('_design/basicStats' in db)
        self.assertTrue('jobs' in db['_design/manage']['views'])
        self.assertTrue('addCar' in db['_design/basicStats']['views'])
        self.assertTrue('deleteCar' in db['_design/basicStats']['views'])
        
        self.sp.deleteProject(self.projName)
        self.assertFalse( self.sp.projectExists(self.projName) )
    

if __name__ == '__main__':
    unittest.main()
