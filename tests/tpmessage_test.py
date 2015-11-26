import logging
import os
import select
import socket
import sys
import time
import unittest
sys.path.append(os.path.abspath('src'))
import tplogger
from tpmessage import TPMessage
logger = tplogger.getTPLogger('tpmessage_test.log', logging.DEBUG)
class TPMessageTest(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass
    def test_pack(self):
        m = TPMessage()
        m.method = TPMessage.METHOD_ASKREADY
        b = m.pack()
        self.assertTrue(b == b'\x00\x00\x00\x01')
        pass
    def test_unpack(self):
        m = TPMessage()
        m.unpack(b'\x00\x00\x00\x01')
        self.assertTrue(m.method == TPMessage.METHOD_ASKREADY)
        pass
    def test_pack_unpack(self):
        s1, s2 = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        m = TPMessage()
        m.method = TPMessage.METHOD_ASKREADY
        b1 = m.pack()
        s1.sendall(b1)
        bufsize = 4096
        b2 = s2.recv(bufsize)
        s1.close()
        s2.close()
        n = TPMessage()
        n.unpack(b2)
        self.assertTrue(n.method == m.method)
        pass
    pass

