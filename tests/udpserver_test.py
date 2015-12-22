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

def UDPServerTestPickleJar_Handshake(resend, timeout, client, svrsock, q):
    res = client.Handshake(svrsock, resend, timeout)
    svrsock.Close()
    q.put(res)

def UDPServerTestPickleJar_Run(tries, resend, timeout, c, svraddr, r, k, q):
    result = False
    try:
        result = c.Run(svraddr, r, k, None, tries, resend, timeout)
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
        # to do: if this fails intermittently, retry when client dies.
        qs = []
        ps = []
        svrs = []
        clients = []
        timeout = 1
        resend = 1
        # Spawn clients.
        for i in range(0, n):
            csock, ssock = UDPSocket.Pair()
            cesock = UDPEventSocket(csock)
            sesock = UDPEventSocket(ssock)
            client = UDPClient()
            q = multiprocessing.Queue()
            p = multiprocessing.Process(target=\
                    UDPServerTestPickleJar_Handshake,
                    args=(resend, timeout, client, sesock, q))
            p.start()
            qs.append(q)
            ps.append(p)
            clients.append(cesock)
            svrs.append(sesock)
        conf = GameConfig()
        server = UDPServer()
        status = server.Handshake(clients, conf, timeout)
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
        k = NullKeyboard()
        r = NullRenderer()
        conf = GameConfig()
        conf.player_size = n
        conf.game_length = 0
        # Prevent engine from running for 30 seconds after the end of game.
        conf.frames_per_sec = 0
        # Try to avoid the case with a client dying at the end of handshake.
        test_tries = 20
        status = 0
        for i in range(0, test_tries):
            s = UDPSocket()
            s.Open()
            s.Bind(('', 0))
            svraddr = s.sock.getsockname()
            ps = []
            qs = []
            clients = []
            server_tries = 100
            server_timeout = 60
            client_tries = 60
            client_resend = 1
            client_timeout = 2.0
            for i in range(0, n):
                q = multiprocessing.Queue()
                c = UDPClient()
                p = multiprocessing.Process(target=\
                        UDPServerTestPickleJar_Run,
                        args=(client_tries, client_resend, client_timeout, 
                            c, svraddr, r, k, q))
                p.start()
                ps.append(p)
                qs.append(q)
            svr = UDPServer()
            status = svr.Run(s, False, conf, server_tries, server_timeout)
            results = []
            for i in range(0, n):
                results.append(qs[i].get())
                ps[i].join()
            s.Close()
            if status == 0:
                break
        self.assertTrue(status == 0,
                'Handshake did not complete with all clients alive.')
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
