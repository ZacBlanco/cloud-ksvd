import unittest
import sys
import json
import zlib
import random
import struct
import time
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

    @patch('socket.socket.sendto', side_effect=[1, -1, 5, -1])
    def test_mocked_send(self, mock1):
        c1 = Communicator('udp', 10001)
        self.assertEqual(c1.send('192.168.1.1', 'ayyy'.encode('utf-8'), 'noice'), True)
        self.assertEqual(c1.send('192.168.1.1', 'ayyy'.encode('utf-8'), 'noice'), False)
        self.assertEqual(c1.send('192.168.1.1', 'ayyy'.encode('utf-8'), 'noice'), True)
        self.assertEqual(c1.send('192.168.1.1', 'ayyy'.encode('utf-8'), 'noice'), False)
        c1.close()

    @patch('socket.socket.sendto', return_value=5)
    def test_big_mock_send(self, mock1):
        l = str(list(range(1000))).encode('utf-8')
        c1 = Communicator('udp', 10001)
        self.assertEqual(c1.send('abc1213', l, 'big_'), True)
        mock1.return_value=-1
        self.assertEqual(c1.send('abc1213', l, 'big_'), False)
        c1.close()
    

    def test_get(self):
        # Encodes and decodes a single packet.
        c1 = Communicator('udp', 10001)
        l = str(list(range(100))).encode('utf-8')
        for packet in c1.create_packets(l, '_get'):
            c1.receive(packet, 'test')
        r = c1.get('test', '_get')
        self.assertNotEqual(r, None)
        self.assertEqual(l, r, 'Reassembled bytes should be the same.')
        c1.close()

    def test_create_large(self):
        # This test helped to fix a bug where we were accidentally appending an extra blank packet when creating packets
        c1 = Communicator('udp', 10001)
        l = str(list(range(550))).encode('utf-8')
        packets = c1.create_packets(l, '_get')
        self.assertEqual(len(packets), 6)

        c1.close()

    def test_large_get(self):
        # This test assures that packets split into multiple pieces and received are able to be reassembled corectly.
        c1 = Communicator('udp', 10001)
        l = str(list(range(1000))).encode('utf-8')
        # print(l)
        packets = c1.create_packets(l, '_get')
        for packet in packets:
            c1.receive(packet, 'test')
        r = c1.get('test', '_get')
        self.assertNotEqual(r, None)
        self.assertEqual(l, r, 'Reassembled bytes should be the same.')
        c1.close()

    @patch('socket.socket.recvfrom')
    def test_mock_listen(self, mock1):
        l = str(list(range(20))).encode('utf-8')
        d = struct.pack('H', 0)
        d += d
        d += 'test'.encode('utf-8')
        d += l
        mock1.return_value = (d, ('127.0.0.1', 9071))
        c1 = Communicator('udp', 9071)
        c1.listen()
        self.assertNotEqual(c1.listen_thread, None)
        self.assertEqual(c1.is_listening, True)
        c1.receive = MagicMock()
        c1.send('127.0.0.1', l, 'test')
        
        # Give some time for the other thread to run before checking conditions
        ctr = 0
        while mock1.called != True and c1.receive.called != True and ctr < 20:
            time.sleep(0.1)
        
        mock1.assert_called_with(1024)
        c1.close()
        c1.receive.assert_called_with(d, '127.0.0.1')

    def test_same_tag_send(self):


        c1 = Communicator('udp', 9071)
        for i in range(10):
            msg = 'Iteration: {}'.format(i).encode('utf-8')
            packets = c1.create_packets(msg, 'test')
            for packet in packets:
                c1.receive(packet, 'local')
            self.assertEqual(c1.get('local', 'test').decode('utf-8'), msg.decode('utf-8'))
            

        c1.close()
        
    def test_multi_get(self):

        c1 = Communicator('udp', 9071)
        s = bytes(str(range(1000)).encode('utf-8'))
        pkts = c1.create_packets(s ,'tg11')
        for pkt in pkts:
            c1.receive(pkt, 'local')
        s2 = c1.get('local', 'tg11')
        self.assertEqual(s, s2, "Bytes should be able to be retrieved")
        s2 = c1.get('local', 'tg11')
        self.assertNotEqual(s2, s, "Should not be able to retrieve the same data again")
        c1.close()
        



        
        
