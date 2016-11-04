import unittest, sys
sys.path.append('..')

import cloud_comm as comm
from cloud_comm import Communicator


class TestCommModuleMethods(unittest.TestCase):

    def test_get_mtu(self):
        m1 = comm.get_mtu()
        self.assertEqual(m1, 576)

    def test_port_str(self):
        p = ''
        with self.assertRaises(TypeError):
            comm.check_port(p)
        
    def test_port_ltz(self):
        p = -1
        with self.assertRaises(ValueError):
            comm.check_port(p)

    def test_port_gtsf(self):
        p = 65536
        with self.assertRaises(ValueError):
            comm.check_port(p)

    def test_port_valid(self):
        self.assertEqual(comm.check_port(8080), True)
        self.assertEqual(comm.check_port(10000), True)


class TestCommunicator(unittest.TestCase):

    def test_bad_init(self):
        '''Test constructors with bad parameters
        Don't need to close b/c we never actually create an object.
        '''
        with self.assertRaises(ValueError):
            c1 = Communicator('uasd', 9090)

        with self.assertRaises(ValueError):
            c1 = Communicator('udp', 90000)

        with self.assertRaises(TypeError):
            c1 = Communicator('UDP', '123')
        
        with self.assertRaises(ValueError):
            c1 = Communicator('udp', -1)
        
        with self.assertRaises(NotImplementedError):
            c1 = Communicator('tcp', 10000)

    def test_init(self):

        c1 = Communicator('UDP', 9887)
        self.assertEqual(c1.listen_port, 9887)
        self.assertEqual(c1.send_port, 9887)
        self.assertEqual(c1.is_listening, False)
        self.assertEqual(c1.listen_thread, None)
        self.assertEqual(c1.is_open, True)
        self.assertEqual(c1.mtu, comm.get_mtu())
        
        c1.close()

