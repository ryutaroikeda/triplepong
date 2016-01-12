import logging
import multiprocessing
import os
import sys
import unittest
sys.path.append(os.path.abspath('src'))
import tplogger
from udpsocket import UDPSocket
from udpdatagram import UDPDatagram
logger = tplogger.getTPLogger('udpsocket_test.log', logging.DEBUG)
def UDPSocketTestPickleJar_Accept(sock, q):
    try:
        conn = sock.Accept(1)
        addr = conn.sock.getpeername()
    except Exception as e:
        logger.exception(e)
        addr = ('',0)
    q.put(addr)

class UDPSocketTest(unittest.TestCase):
    def template_IsMoreRecent(self, s1, s2, expected):
        s = UDPSocket()
        res = s.IsMoreRecent(s1, s2, UDPDatagram.MAX_SEQ)
        self.assertTrue(res == expected)

    def template_UpdateAck(self, ack, ackbits, update, expected_ack, 
            expected_ackbits):
        s= UDPSocket()
        s.ack = ack
        s.ackbits = ackbits
        s.UpdateAck(update)
        self.assertTrue(s.ack == expected_ack)
        self.assertTrue(s.ackbits == expected_ackbits)

    def template_SendAndRecv(self, seq, ack, ackbits, payload,
            expected_ack, expected_ackbits):
        s = UDPSocket()
        t = UDPSocket()
        s.Open()
        t.Open()
        s_addr = ('127.0.0.1', 5555)
        t_addr = ('127.0.0.1', 2056)
        s.Bind(s_addr)
        t.Bind(t_addr)
        s.sock.connect(t_addr)
        t.sock.connect(s_addr)
        s.seq = seq
        t.ack = ack
        t.ackbits = ackbits
        status = 0
        try:
            s.Send(payload)
            for i in range(0, 1000):
                d = t.Recv()
                if d != None:
                    break
        except Exception as ex:
            logger.exception(ex)
            status = 1
        s.Close()
        t.Close()
        self.assertTrue(status == 0)
        self.assertTrue(s.seq == seq + 1)
        self.assertTrue(d != None)
        self.assertTrue(d.seq == seq)
        self.assertTrue(d.ackbits == ackbits)
        self.assertTrue(d.payload == payload)
        self.assertTrue(t.ack == expected_ack)
        self.assertTrue(t.ackbits == expected_ackbits,
                'got {0} expected {1}'.format(t.ackbits, expected_ackbits))

    def test_init(self):
        sock = UDPSocket()
        self.assertTrue(sock.sock == None)
        self.assertTrue(sock.seq == 0)
        self.assertTrue(sock.ack == 0)
        self.assertTrue(sock.ackbits == 0)

    def test_IsMoreRecent_1(self):
        self.template_IsMoreRecent(0, 0, False)

    def test_IsMoreRecent_2(self):
        self.template_IsMoreRecent(1, 0, True)

    def test_IsMoreRecent_3(self):
        self.template_IsMoreRecent(UDPDatagram.MAX_SEQ - 1, 0, False)

    def test_IsMoreRecent_4(self):
        self.template_IsMoreRecent(0, UDPDatagram.MAX_SEQ - 1, True)

    def test_UpdateAck_1(self):
        self.template_UpdateAck(0, int('0'*32,2), 0, 0, int('0'*32,2))

    def test_UpdateAck_2(self):
        self.template_UpdateAck(0, int('0101'*8,2), 0, 0, int('0101'*8,2))

    def test_UpdateAck_3(self):
        self.template_UpdateAck(0, int('0'*32,2), 1, 1, int('1'+'0'*31,2))

    def test_UpdateAck_4(self):
        self.template_UpdateAck(0, int('0'*32,2), 2, 2, int('01'+'0'*30,2))

    def test_UpdateAck_5(self):
        self.template_UpdateAck(0, int('0'*32,2), 32, 32, int('0'*31+'1',2))

    def test_UpdateAck_6(self):
        self.template_UpdateAck(0, int('0'*32,2), 33, 33, int('0'*32,2))

    def test_UpdateAck_7(self):
        self.template_UpdateAck(33, int('0'*32,2), 0, 33, int('0'*32,2))

    def test_UpdateAck_8(self):
        self.template_UpdateAck(32, int('0'*32,2), 0, 32, int('0'*31+'1',2))

    def test_UpdateAck_9(self):
        self.template_UpdateAck(UDPDatagram.MAX_SEQ - 1, int('0'*31+'1',2),
                0, 0, int('1'+'0'*31,2))

    def test_UpdateAck_10(self):
        self.template_UpdateAck(0, int('0'*31+'1',2), UDPDatagram.MAX_SEQ - 1,
                0, int('1'+'0'*30+'1',2))

    def test_SendAndRecv_1(self):
        self.template_SendAndRecv(0, 0, int('0'*32,2),
                b'0'*UDPDatagram.MAX_PAYLOAD, 0, int('0'*32,2))

    def test_SendAndRecv_2(self):
        self.template_SendAndRecv(1, 0, int('0'*32,2),
                b'1'*UDPDatagram.MAX_PAYLOAD, 1, int('1'+'0'*31,2))

    def test_Recv_IgnoreOld_1(self):
        s, t = UDPSocket.Pair()
        tries = 20
        count = 0
        t.should_ignore_old = True
        status = 0
        try:
            for i in range(0, tries):
                s.seq = 1
                s.Send(b'')
            for i in range(0, tries):
                e = t.Recv()
                if e != None:
                    count += 1
        except Exception as ex:
            logger.exception(ex)
            status = 1
        s.Close()
        t.Close()
        self.assertTrue(status == 0)
        self.assertTrue(count == 1, 'Counted {0}'.format(count))

    def test_ConnectAndAccept(self):
        sock = UDPSocket()
        sock.Open()
        sock.Bind(('', 10000))
        q = multiprocessing.Queue()
        p = multiprocessing.Process(target=UDPSocketTestPickleJar_Accept,
                args=(sock, q))
        p.start()
        status = 0
        try:
            client = UDPSocket()
            client.Open()
            client.Connect(('127.0.0.1', 10000), 1)
        except Exception as ex:
            logger.exception(ex)
            status = 1
        client_name = q.get()
        expected_sock_name = client.sock.getsockname()
        p.join()
        sock.Close()
        client.Close()
        self.assertTrue(expected_sock_name == client_name)

    def test_Pair_1(self):
        p, q = UDPSocket.Pair()
        status = 0
        try:
            p_name = p.sock.getsockname()
            p_peer = p.sock.getpeername()
            q_name = q.sock.getsockname()
            q_peer = q.sock.getpeername()
        except Exception as ex:
            logger.exception(ex)
            status = 1
        p.Close()
        q.Close()
        self.assertTrue(status == 0)
        self.assertTrue(p_name == q_peer)
        self.assertTrue(p_peer == q_name)
        self.assertTrue(p.ttl == UDPSocket.MAX_TIME_TO_LIVE)
        self.assertTrue(q.ttl == UDPSocket.MAX_TIME_TO_LIVE)

