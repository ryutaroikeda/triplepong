import multiprocessing
import os
import signal
import socket
import sys
import unittest
sys.path.append(os.path.abspath('src'))
from server import TPServer
from client import TPClient
# This class provides access to methods that are targets of spawned processes 
# in TPServerTest. According to 
# http://stackoverflow.com/questions/25646382/python-3-4-multiprocessing-does-
# not-work-with-unittest
# unittest.TestCase is not pickleable (i.e. serializable) as of at least 
# Python 3.4. 
class TPServerTestPickleJar(object):
    def __init__(self):
        pass
    def svrhandshake(self, svrsock, q):
        s = TPServer()
        cs = [svrsock]
        s.handshake(cs)
        q.put(cs)
        pass
    pass

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
        # spawn a process and share cs
        q = multiprocessing.Queue()
        jar = TPServerTestPickleJar()
        svrp = multiprocessing.Process(target=jar.svrhandshake,
                args=(svrsock,q,))
        svrp.start()
        c.handshake(clientsock)
        result = q.get()
        svrp.join() # wait for server to finish
        svrsock.close()
        clientsock.close()
        self.assertTrue(result == [svrsock])
        pass
    pass




