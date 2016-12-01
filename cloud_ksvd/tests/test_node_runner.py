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
        n.task_running.value = 1
        r1 = self.app.get('/start/consensus')
        self.assertEqual(mock1.called, False, "process start() should *not* have been called.")
        n.task_running.value = 0

    @mock.patch('requests.get')
    @mock.patch('time.sleep')
    def test_kickoff(self, mock2, mock1):
        task = n.task_running
        n.kickoff(task)
        self.assertEqual(mock1.call_count, 5)
        mock1.assert_any_call('http://192.168.2.180:9090/start/consensus')
        mock1.assert_any_call('http://192.168.2.181:9090/start/consensus')
        mock1.assert_any_call('http://192.168.2.182:9090/start/consensus')
        mock1.assert_any_call('http://192.168.2.183:9090/start/consensus')
        mock1.assert_any_call('http://192.168.2.184:9090/start/consensus')
        self.assertEqual(mock2.called, True, "at this point time.sleep() should have been called.")

    def test_load_data(self):
        data = n.data_loader('vectors.txt')

        for i in range(3):
            for j in range(5):
                self.assertEqual(data[i][j], i+1, "Should be equal to i+1")

    @mock.patch('consensus.get_ip_address', side_effect=['192.168.2.180','192.168.2.181', "192.168.2.182", "192.168.2.183", "192.168.2.184"])
    def test_get_neighbors(self, mock1):
        neighbors = n.get_neighbors()
        print(neighbors)

        neighbors = n.get_neighbors()
        print(neighbors)

        neighbors = n.get_neighbors()
        print(neighbors)

        neighbors = n.get_neighbors()
        print(neighbors)

        neighbors = n.get_neighbors()
        print(neighbors)



        
