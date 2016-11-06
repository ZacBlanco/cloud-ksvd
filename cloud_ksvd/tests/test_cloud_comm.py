import unittest
import sys
import json
import zlib
import random
import struct
from unittest.mock import MagicMock, patch

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

    def test_close(self):
        c1 = Communicator('UDP', 9887)
        self.assertEqual(c1.is_open, True)
        self.assertEqual(c1.is_listening, False)
        self.assertNotEqual(c1.listen_sock, None)
        self.assertNotEqual(c1.send_sock, None)

        c1.close()
        self.assertEqual(c1.is_open, False)
        self.assertEqual(c1.is_listening, False)
        self.assertNotEqual(c1.listen_sock, None)
        self.assertNotEqual(c1.send_sock, None)

    def test_double_close(self):
        c1 = Communicator('UDP', 9090)
        c1.close()
        with self.assertRaises(BrokenPipeError):
            c1.close()

    def test_payload(self):
        l = []
        for i in range(10):
            l.append(i)
        data = {'hello': 'world',
                'test': l}
        data1 = json.dumps(data, separators=[':', ',']).encode('utf-8')
        self.assertEqual(data1, comm.get_payload(data))

    def test_packet_create_single(self):
        l = []
        for i in range(100):
            l.append(i)
        c1 = Communicator('UDP', 9090)
        l = str(l).encode('utf-8')
        p1 = c1.create_packets(l, '9012')
        self.assertEqual(len(p1), 1)
        p1 = p1[0]
        c1.close()

    def test_large_packet(self):
        c1 = Communicator('udp',10001)
        d = []
        for i in range(1000):
            d.append(random.random())
        d = str(d).encode('utf-8')
        packs = c1.create_packets(d, 'tag1')
        r = bytes() # total data bytes
        t = bytes()
        for packet in packs:
            # print("Packet Size: {}".format(len(packet)))
            r += packet[8:]
            t += packet
            
        # print(len(d))
        # print(len(r))
        self.assertEqual(len(d), len(r))
        self.assertEqual(len(d), len(t) - 8*len(packs))
        for i in range(len(packs)):
            seq = struct.unpack('H', packs[i][2:4])[0]
            t = struct.unpack('H', packs[i][0:2])[0]
            self.assertEqual(seq, i)
            self.assertEqual(t, len(packs) - 1)
        c1.close()    

    def test_single_packet(self):
        c1 = Communicator('udp', 8080)
        d = []
        for i in range(122): # Exactly 500 bytes
            d.append(i)
        d = str(d).encode('utf-8')
        d = c1.create_packets(d, '1111')
        self.assertEqual(len(d), 1, 'Should have only created a single packet')
        self.assertEqual('1111', d[0][4:8].decode('utf-8'))
        self.assertEqual(0, struct.unpack('H', d[0][0:2])[0])
        self.assertEqual(0, struct.unpack('H', d[0][2:4])[0])
        c1.close()

    def test_close_ops(self):
        c1 = Communicator('UDP', 80)
        c1.close()

        with self.assertRaises(BrokenPipeError):
            c1.listen()

        with self.assertRaises(BrokenPipeError):
            c1.send(bytes(), 'lol', 'test')

    def test_mocked_send(self):
        c1 = Communicator('udp', 10001)

        c1.send('192.168.1.1', 'ayyy'.encode('utf-8'), 'noice')

        c1.close()

        
        
