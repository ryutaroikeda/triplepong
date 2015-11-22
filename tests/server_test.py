import os
import signal
import socket
import sys
import threading
import unittest
sys.path.append(os.path.abspath('src'))
from server import TPServer
from client import TPClient
class TPServerTest(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass
    def test_handshake_one_client(self):
        addr = ('127.0.0.1', 8080)
        svrsock, clientsock = socket.socketpair(
                socket.AF_UNIX, socket.SOCK_STREAM)
        s = TPServer()
        c = TPClient()
        # spawn a thread and share cs
        cs = [svrsock] 
        def svrhandshake():
            s = TPServer()
            s.handshake(cs)
            pass
        th = threading.Thread(target=svrhandshake)
        th.run()
        c.handshake(clientsock)
        th.join() # wait for th to finish
        svrsock.close()
        clientsock.close()
        self.assertTrue(cs.__len__ == 1)
        pass
    pass




