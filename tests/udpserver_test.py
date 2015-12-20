import multiprocessing
import os
import sys
import unittest
sys.path.append(os.path.abspath('src'))
from udpclient import UDPClient
from udpeventsocket import UDPEventSocket
from udpserver import UDPServer
from udpsocket import UDPSocket
def UDPServerTestPickleJar_AcceptN(svr, svrsock, n, q):
    socks = []
    svr.AcceptN(svrsock, socks, n)
    svrsock.Close()
    q.put(len(socks))

def UDPServerTestPickleJar_Handshake(client, svrsock, q):
    res = client.Handshake(svrsock, 1)
    svrsock.Close()
    q.put(res)

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

    def template_Handshake(self, n):
        qs = []
        ps = []
        svrs = []
        clients = []
        # Spawn clients.
        for i in range(0, n):
            csock, ssock = UDPSocket.Pair()
            cesock = UDPEventSocket(csock)
            sesock = UDPEventSocket(ssock)
            client = UDPClient()
            q = multiprocessing.Queue()
            p = multiprocessing.Process(target=\
                    UDPServerTestPickleJar_Handshake, args=(client, sesock, q))
            p.start()
            qs.append(q)
            ps.append(p)
            clients.append(cesock)
            svrs.append(sesock)
        server = UDPServer()
        server.Handshake(clients, 10)
        res = []
        for i in range(0, n):
            res.append(qs[i].get())
            ps[i].join()
        for s in svrs:
            s.Close()
        for c in clients:
            c.Close()
        for i in range(0, n):
            self.assertTrue(res[i])
    
    def test_AcceptN_1(self):
        self.template_AcceptN(0)
    
    def test_AcceptN_2(self):
        self.template_AcceptN(1)
    
    def test_AcceptN_3(self):
        self.template_AcceptN(2)
    
    def test_AcceptN_4(self):
        self.template_AcceptN(3)
    
    def test_Handshake_1(self):
        self.template_Handshake(0)
    
    def test_Handshake_2(self):
        self.template_Handshake(1)
    
    def test_Handshake_3(self):
        self.template_Handshake(2)

    def test_Handshake_4(self):
        self.template_Handshake(3)

