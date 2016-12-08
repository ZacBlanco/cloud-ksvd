import sys
import unittest
import tempfile
import os
from unittest import mock
from unittest.mock import MagicMock, patch
sys.path.append('..')
import node_runner as n
import consensus

n.CONF_FILE = 'params_test.conf'

class test_node_runner(unittest.TestCase):
    
    def setUp(self):
        self.db_fd, n.APP.config['DATABASE'] = tempfile.mkstemp()
        n.APP.config['TESTING'] = True
        self.app = n.APP.test_client()
        # with n.APP.app_context():
        #     n.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(n.APP.config['DATABASE'])

    def test_get_degree(self):
        d1 = self.app.get('/degree?host=192.168.2.180')
        self.assertEqual(int(d1.get_data()), 1, "Degree of 2.180 should be 1")
        
        d1 = self.app.get('/degree?host=192.168.2.181')
        self.assertEqual(int(d1.get_data()), 3, "Degree of 2.181 should be 3")

        d1 = self.app.get('/degree?host=192.168.2.182')
        self.assertEqual(int(d1.get_data()), 3, "Degree of 2.182 should be 3")
        
        d1 = self.app.get('/degree?host=192.168.2.183')
        self.assertEqual(int(d1.get_data()), 4, "Degree of 2.183 should be 4")

        d1 = self.app.get('/degree?host=192.168.2.184')
        self.assertEqual(int(d1.get_data()), 3, "Degree of 2.184 should be 3")

    @mock.patch('multiprocessing.Process.start')
    def test_consensus_start(self, mock1):
        r1 = self.app.get('/start/consensus')
        self.assertEqual(mock1.called, True, "process start() should have been called.")

        mock1.reset_mock()
        n.TASK_RUNNING.value = 1
        r1 = self.app.get('/start/consensus')
        self.assertEqual(mock1.called, False, "process start() should *not* have been called.")
        n.TASK_RUNNING.value = 0

    @mock.patch('node_runner.data_loader', return_value=MagicMock())
    @mock.patch('consensus.get_ip_address', return_value='192.168.2.180')
    @mock.patch('consensus.get_weights', return_value={'192.168.2.183': 0.5})
    @mock.patch('requests.get')
    @mock.patch('time.sleep')
    def test_kickoff(self, mock2, mock1, mock3, mock4, mock5):
        consensus.run = MagicMock()
        task = n.TASK_RUNNING
        n.kickoff(task, 20)
        self.assertEqual(mock1.call_count, 5)
        mock1.assert_any_call('http://192.168.2.180:9090/start/consensus?tc=20')
        mock1.assert_any_call('http://192.168.2.181:9090/start/consensus?tc=20')
        mock1.assert_any_call('http://192.168.2.182:9090/start/consensus?tc=20')
        mock1.assert_any_call('http://192.168.2.183:9090/start/consensus?tc=20')
        mock1.assert_any_call('http://192.168.2.184:9090/start/consensus?tc=20')

        
    def test_load_data(self):
        data = n.data_loader('vectors.txt')

        for i in range(3):
            for j in range(5):
                self.assertEqual(data[i][j], i+1, "Should be equal to i+1")

    @mock.patch('consensus.get_ip_address', side_effect=['192.168.2.180','192.168.2.181', "192.168.2.182", "192.168.2.183", "192.168.2.184"])
    def test_get_neighbors(self, mock1):
        neighbors = n.get_neighbors()
        self.assertEqual(len(neighbors), 1, "Neighbors should be 2 on 2.180")

        neighbors = n.get_neighbors()
        self.assertEqual(len(neighbors), 3, "Neighbors should be 3 on 2.181")

        neighbors = n.get_neighbors()
        self.assertEqual(len(neighbors), 3, "Neighbors should be 3 on 2.182")

        neighbors = n.get_neighbors()
        self.assertEqual(len(neighbors), 4, "Neighbors should be 4 on 2.183")

        neighbors = n.get_neighbors()
        self.assertEqual(len(neighbors), 3, "Neighbors should be 3 on 2.184")



        
