#!/usr/bin/python
import unittest, xmlrpclib, couchdb, couchdb.client
from ConfigParser import SafeConfigParser

class Test(unittest.TestCase):

    def setUp(self):
        configFiles = ('../config/common.ini', '../config/rpc_client.ini')
    
        self.cfg = SafeConfigParser()
        self.cfg.read(configFiles)
        host = self.cfg.get('rpc-client', 'server')
        port = self.cfg.getint('rpc-server', 'port')
        connString = 'http://%s:%i' % (host, port)
        self.sp = xmlrpclib.ServerProxy(connString)
        self.projName = 'test_project_abracadabra'
        self.jobName = 'test_job_foo'
        
        f = open('../models/test_model_1.yaml','r')
        self.yamlModel = f.read(-1)
        f.close()
        
        # Clean up if previous session had some problems and there are leftovers.
        if self.sp.projectExists(self.projName):
            self.sp.deleteProject(self.projName)


    def test_projectExists(self):
        ex = self.sp.projectExists(self.projName)
        self.assertFalse(ex)
        
        
    def test_createAndDeleteProject(self):
        self.assertFalse( self.sp.projectExists(self.projName) )
        self.sp.createProject(self.projName)
        self.assertTrue( self.sp.projectExists(self.projName) )
        self.sp.deleteProject(self.projName)
        self.assertFalse( self.sp.projectExists(self.projName) )
        
    def test_createViews(self):
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
    
    def test_newProjectId(self):
        self.sp.createProject(self.projName)
        self.assertTrue( self.sp.projectExists(self.projName) )
        
        self.assertEqual(self.sp.getNewJobId(self.projName), 1)
        self.assertEqual(self.sp.getNewJobId(self.projName), 2)
        self.assertEqual(self.sp.getNewJobId(self.projName), 3)
        self.assertEqual(self.sp.getNewJobId(self.projName), 4)
        self.assertEqual(self.sp.getNewJobId(self.projName), 5)
        
        self.sp.deleteProject(self.projName)
        self.assertFalse( self.sp.projectExists(self.projName) )
        
    def test_addJobAndExistence(self):
        self.sp.createProject(self.projName)
        self.assertTrue( self.sp.projectExists(self.projName) )

        self.assertFalse(self.sp.jobExists(self.projName, self.jobName))        
        self.sp.addJob(self.projName, self.jobName, self.yamlModel)
        self.assertTrue(self.sp.jobExists('rns_16', 'rns_16'))
        
        self.sp.deleteProject(self.projName)
        self.assertFalse( self.sp.projectExists(self.projName) )
        
    def test_deleteJob(self):
        self.sp.createProject(self.projName)
        self.assertTrue( self.sp.projectExists(self.projName) )

        self.assertFalse(self.sp.jobExists(self.projName, self.jobName))        
        self.sp.addJob(self.projName, self.jobName, self.yamlModel)
        self.assertTrue(self.sp.jobExists(self.projName, self.jobName))
        
        server = couchdb.Server(self.cfg.get('couchdb', 'dbaddress'))
        db = server[self.projName]
        self.assertTrue('j1' in db)
        self.assertTrue('j1Progress' in db)
        self.sp.simulate(self.projName, 1)
        self.assertTrue('s1_0.0' in db)
        
        self.sp.deleteJob(self.projName, self.jobName)
        self.assertFalse(self.sp.jobExists(self.projName, self.jobName))
        self.assertFalse('j1' in db)
        self.assertFalse('j1Progress' in db)
        self.assertFalse('s1_0.0' in db)
        
        self.sp.deleteProject(self.projName)
        self.assertFalse( self.sp.projectExists(self.projName) )
        

if __name__ == '__main__':
    unittest.main()
