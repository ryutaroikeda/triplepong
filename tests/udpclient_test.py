import os
import sys
import unittest
sys.path.append(os.path.abspath('src'))
from udpclient import UDPClient
from udpeventsocket import UDPEventSocket
from udpsocket import UDPSocket
class UDPClientTest(unittest.TestCase):
    @unittest.skip('deprecate')
    def test_Handshake_1(self):
        client = UDPClient()
        svr = UDPEventSocket(None)
        result = client.Handshake(svr, 1)
        self.assertTrue(result == False)

    @unittest.skip('deprecate')
    def test_Handshake_2(self):
        client = UDPClient()
        ssock = UDPSocket()
        svr = UDPEventSocket(ssock)
        result = client.Handshake(svr, 1)
        self.assertTrue(result == False)
