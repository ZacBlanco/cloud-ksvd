import sys
import unittest
import os
import pickle
import numpy as np
sys.path.append('..')

import consensus
from cloud_comm import Communicator
from unittest.mock import MagicMock, patch



def good_resp(d):
    r = MagicMock()
    r.text = d
    r.status_code = 200
    return r

def bad_resp():
    r = MagicMock()
    r.status_code = 500
    return r


class ConsensusTest(unittest.TestCase):

    @patch('consensus.transmit', return_value=MagicMock())
    @patch('consensus.receive', return_value={ 'local': pickle.dumps(np.zeros((2, 2))), 'local2': pickle.dumps(np.ones((2, 2))) })
    def test_consensus_test(self, mock2, mock1):
        a = np.zeros((2, 2))
        a[0][0] = 14
        a[0][1] = 17
        a[1][0] = 8
        a[1][1] = 35
        comm = Communicator('udp', 12309)
        r = consensus.run(a, 50, 12, {'local': 1/3, 'local2': 1/3 }, comm)
        # print("Final Results: {}".format(r))
        comm.close()


    def test_m2b(self):
        t1 = np.zeros((2, 2))
        t1[0][1] = 5
        mb = consensus.matrix_to_bytes(t1)
        self.assertEqual(type(mb), bytes, "Type of matrix should be bytes")
        back = consensus.matrix_from_bytes(mb)
        self.assertEqual(t1[0][0], back[0][0], "Objects should be equal after reconstructing from bytes")
        self.assertEqual(t1[0][1], back[0][1], "Objects should be equal after reconstructing from bytes")
        self.assertEqual(t1[1][0], back[1][0], "Objects should be equal after reconstructing from bytes")
        self.assertEqual(t1[1][1], back[1][1], "Objects should be equal after reconstructing from bytes")

    @patch('requests.get', side_effect=[good_resp(2), good_resp(3), bad_resp()])
    def test_weights(self, mock1):
        neighbors = ['192.168.2.180', '192.168.2.181']
        w = consensus.get_weights(neighbors, 'params_test.conf')
        self.assertEqual(w['192.168.2.180'], 1/3, 'Should have weight of 1/3')
        self.assertEqual(w['192.168.2.181'], 1/4, 'Deg of 3 Should have weight of 1/4')
        self.assertEqual(w['self'], 1-(1/3 + 1/4), "Self should have 1 - sum of other weights")

        w = consensus.get_weights([], 'params_test.conf')
        self.assertEqual(w['self'], 1, "No neighbors equals weight of 1")
        

    def test_build_tag(self):
        id = 1
        num = 333
        tag1 = consensus.build_tag(id, num)

        # Single byte from bytes is interpreted as an int
        id1 = tag1[0]
        # id1 =  int.from_bytes(tag1[0] , byteorder='little')

        num1 = int.from_bytes(tag1[1:], byteorder='little')

        self.assertEqual(id1, id, "Should be able to get ID from tag byte 0")
        self.assertEqual(
            num1, num, "Should be able to get num from tag byte 1-4")

        id = 257
        tag1 = consensus.build_tag(id, num)
        self.assertEqual(
            tag1[0], 1, "id should be modulus 256 of original value")

        id = 1
        num = 2**(24) + 2
        tag1 = consensus.build_tag(id, num)
        num1 = int.from_bytes(tag1[1:], byteorder='little')
        self.assertEqual(num % 2**24, num1, "Number should be modulus of 2^24")
