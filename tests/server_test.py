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
# This seems to not be an issue on Python 3.5
class TPServerTestPickleJar(object):
    def __init__(self):
        pass
    def svrhandshake1(self, svrsock, q):
        s = TPServer()
        cs = [svrsock]
        s.handshake(cs)
        q.put(cs.__len__())
        pass
    def acceptAndHandshake(self, svrsock, clientNum, q):
        s = TPServer()
        socks = s.acceptN(svrsock, clientNum)
        s.handshake(socks)
        q.put(socks.__len__())
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
        c = TPClient()
        # spawn a process and share cs
        q = multiprocessing.Queue()
        jar = TPServerTestPickleJar()
        svrp = multiprocessing.Process(target=jar.svrhandshake1,
                args=(svrsock,q,))
        svrp.start()
        c.handshake(clientsock)
        result = q.get()
        svrp.join() # wait for server to finish
        svrsock.close()
        clientsock.close()
        self.assertTrue(result == 1)
        pass
    def test_handshake_two_clients_sequence(self):
        addr = ('127.0.0.1', 8080)
        c1 = TPClient()
        c2 = TPClient()
        q = multiprocessing.Queue()
        jar = TPServerTestPickleJar()
        svrsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        svrsock.bind(addr)
        svrsock.listen(2)
        svrp = multiprocessing.Process(target=jar.acceptAndHandshake,
                args=(svrsock,2,q,))
        svrp.start()
        csock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        csock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        csock1.connect(addr)
        csock2.connect(addr)
        c1.handshake(csock1)
        c2.handshake(csock2)
        result = q.get()
        c1.close()
        c2.close()
        svrp.join()
        self.assertTrue(result == 2)
        pass
    pass

