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
        self.template_IsMoreRecent(UDPSocket.MAX_SEQ - 1, 0, False)

    def test_IsMoreRecent_4(self):
        self.template_IsMoreRecent(0, UDPSocket.MAX_SEQ - 1, True)

    def test_UpdateAck_1(self):
        self.template_UpdateAck(0, int('0'*32,2), 0, int('0'*32,2))

    def test_UpdateAck_2(self):
        self.template_UpdateAck(0, int('0101'*8,2), 0, int('0101'*8,2))

    def test_UpdateAck_3(self):
        self.template_UpdateAck(0, int('0'*32,2), 1, int('1'+'0'*31,2))

    def test_UpdateAck_4(self):
        self.template_UpdateAck(0, int('0'*32,2), 2, int('01'+'0'*30,2))

    def test_UpdateAck_5(self):
        self.template_UpdateAck(0, int('0'*32,2), 32, int('0'*31+'1',2))

    def test_UpdateAck_6(self):
        self.template_UpdateAck(0, int('0'*32,2), 33, int('0'*32,2))

    def test_UpdateAck_7(self):
        self.template_UpdateAck(33, int('0'*32,2), 0, int('0'*32,2))

    def test_UpdateAck_8(self):
        self.template_UpdateAck(32, int('0'*32,2), 0, int('0'*31+'1',2))

    def test_UpdateAck_9(self):
        self.template_UpdateAck(UDPSocket.MAX_SEQ - 1, int('0'*31+'1',2),
                0, int('1'+'0'*31,2))

    def test_UpdateAck_10(self):
        self.template_UpdateAck(0, int('0'*31+'1',2), UDPSocket.MAX_SEQ - 1,
                int('1'+'0'*30+'1',2))
