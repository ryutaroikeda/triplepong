import multiprocessing
import os
import sys
import unittest
sys.path.append(os.path.abspath('src'))
from udpserver import UDPServer
from udpsocket import UDPSocket
def UDPServerTestPickleJar_AcceptN(svr, svrsock, n, q):
    socks = []
    svr.AcceptN(svrsock, socks, n)
    svrsock.Close()
    q.put(len(socks))

class UDPServerTest(unittest.TestCase):
    def template_AcceptN(self, n):
        ssock = UDPSocket()
        ssock.Open()
        ssock.Bind(('127.0.0.1', 0))
        svr_addr = ssock.sock.getsockname()
        svr = UDPServer()
        q = multiprocessing.Queue()
        p = multiprocessing.Process(target=UDPServerTestPickleJar_AcceptN,
                args=(svr, ssock, n, q))
        p.start()
        for i in range(0, n):
            c = UDPSocket()
            c.Open()
            c.Handshake(svr_addr, 1)
            c.Close()
        connected = q.get()
        p.join()
        ssock.Close()
        self.assertTrue(connected == n)

    def test_AcceptN_1(self):
        self.template_AcceptN(0)

    def test_AcceptN_2(self):
        self.template_AcceptN(1)

    def test_AcceptN_3(self):
        self.template_AcceptN(2)

    def test_AcceptN_4(self):
        self.template_AcceptN(3)
