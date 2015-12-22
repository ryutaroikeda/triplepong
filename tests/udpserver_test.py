import logging
import multiprocessing
import os
import sys
import unittest
sys.path.append(os.path.abspath('src'))
from gameconfig import GameConfig
import tplogger
from udpclient import UDPClient
from udpeventsocket import UDPEventSocket
from udpserver import UDPServer
from udpsocket import UDPSocket
from nullkeyboard import NullKeyboard
from nullrenderer import NullRenderer
logger = tplogger.getTPLogger('udpserver_test.log', logging.DEBUG)
def UDPServerTestPickleJar_AcceptN(timeout, svr, svrsock, n, q):
    socks = []
    svr.AcceptN(svrsock, socks, n, timeout)
    svrsock.Close()
    q.put(len(socks))

def UDPServerTestPickleJar_Handshake(timeout, client, svrsock, q):
    res = client.Handshake(svrsock, timeout)
    svrsock.Close()
    q.put(res)

def UDPServerTestPickleJar_Run(tries, timeout, c, svraddr, r, k, q):
    result = False
    try:
        result = c.Run(svraddr, r, k, None, tries, timeout)
    except Exception as e:
        logger.exception(e)
    q.put(result)

class UDPServerTest(unittest.TestCase):
    def template_AcceptN(self, n):
        ssock = UDPSocket()
        ssock.Open()
        ssock.Bind(('127.0.0.1', 0))
        svr_addr = ssock.sock.getsockname()
        svr = UDPServer()
        timeout = 1.0
        q = multiprocessing.Queue()
        p = multiprocessing.Process(target=UDPServerTestPickleJar_AcceptN,
                args=(timeout, svr, ssock, n, q))
        p.start()
        for i in range(0, n):
            c = UDPSocket()
            c.Open()
            c.Connect(svr_addr, 1)
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
        timeout = 1
        # Spawn clients.
        for i in range(0, n):
            csock, ssock = UDPSocket.Pair()
            cesock = UDPEventSocket(csock)
            sesock = UDPEventSocket(ssock)
            client = UDPClient()
            q = multiprocessing.Queue()
            p = multiprocessing.Process(target=\
                    UDPServerTestPickleJar_Handshake,
                    args=(timeout, client, sesock, q))
            p.start()
            qs.append(q)
            ps.append(p)
            clients.append(cesock)
            svrs.append(sesock)
        conf = GameConfig()
        server = UDPServer()
        server.Handshake(clients, conf, timeout)
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
    
    def template_Run(self, n):
        s = UDPSocket()
        s.Open()
        s.Bind(('', 0))
        svraddr = s.sock.getsockname()
        k = NullKeyboard()
        r = NullRenderer()
        conf = GameConfig()
        conf.player_size = n
        conf.game_length = 0
        # Prevent engine from running for 30 seconds after the end of game.
        conf.frames_per_sec = 0
        ps = []
        qs = []
        clients = []
        tries = 20
        timeout = 2.0
        for i in range(0, n):
            q = multiprocessing.Queue()
            c = UDPClient()
            p = multiprocessing.Process(target=\
                    UDPServerTestPickleJar_Run,
                    args=(tries, timeout, c, svraddr, r, k, q))
            p.start()
            ps.append(p)
            qs.append(q)
        svr = UDPServer()
        svr.Run(s, False, conf, tries, timeout)
        s.Close()
        results = []
        for i in range(0, n):
            results.append(qs[i].get())
            ps[i].join()
        for i in range(0, n):
            self.assertTrue(results[i])

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

    def test_Run_1(self):
        self.template_Run(0)

    def test_Run_2(self):
        self.template_Run(1)

    def test_Run_3(self):
        self.template_Run(2)

    def test_Run_4(self):
        self.template_Run(3)
