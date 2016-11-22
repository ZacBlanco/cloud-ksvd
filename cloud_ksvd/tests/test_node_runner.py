import sys
import unittest
import tempfile
import os
from unittest import mock
from unittest.mock import MagicMock, patch
sys.path.append('..')
import node_runner as n

n.conf_file = 'params_test.conf'

class test_node_runner(unittest.TestCase):
    
    def setUp(self):
        self.db_fd, n.app.config['DATABASE'] = tempfile.mkstemp()
        n.app.config['TESTING'] = True
        self.app = n.app.test_client()
        # with n.app.app_context():
        #     n.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(n.app.config['DATABASE'])

    def test_get_degree(self):
        d1 = self.app.get('/degree?host=192.168.2.180')
        self.assertEqual(int(d1.get_data()), 2, "Degree of 2.180 should be 2")
        
        d1 = self.app.get('/degree?host=192.168.2.181')
        self.assertEqual(int(d1.get_data()), 4, "Degree of 2.181 should be 4")

        d1 = self.app.get('/degree?host=192.168.2.182')
        self.assertEqual(int(d1.get_data()), 4, "Degree of 2.182 should be 4")
        
        d1 = self.app.get('/degree?host=192.168.2.183')
        self.assertEqual(int(d1.get_data()), 5, "Degree of 2.183 should be 5")

        d1 = self.app.get('/degree?host=192.168.2.184')
        self.assertEqual(int(d1.get_data()), 4, "Degree of 2.184 should be 4")

        
