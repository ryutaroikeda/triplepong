import os
import sys
import unittest
sys.path.append(os.path.abspath('src'))
from udpsock import UDPSocket
class UDPSocketTest(unittest.TestCase):
    def template_IsMoreRecent(self, s1, s2, expected):
        s = UDPSocket()
        res = s.IsMoreRecent(s1, s2, s.MAX_SEQ)
        self.assertTrue(res == expected)

    def template_UpdateAck(self, ack, ackbits, update, expected_ackbits):
        s= UDPSocket()
        s.ack = ack
        s.ackbits = ackbits
        s.UpdateAck(update)
        self.assertTrue(s.ackbits == expected_ackbits)

    def test_init(self):
        sock = UDPSocket()
        self.assertTrue(sock.seq == 0)
        self.assertTrue(sock.ack == 0)
        self.assertTrue(sock.ackbits == 0)

    def test_IsMoreRecent_1(self):
        self.template_IsMoreRecent(0, 0, False)

    def test_IsMoreRecent_2(self):
        self.template_IsMoreRecent(1, 0, True)

    def test_IsMoreRecent_3(self):
        self.template_IsMoreRecent((1 << 16) - 1, 0, False)

    def test_IsMoreRecent_4(self):
        self.template_IsMoreRecent(0, (1 << 16) - 1, True)
