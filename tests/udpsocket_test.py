import multiprocessing
import os
import sys
import unittest
sys.path.append(os.path.abspath('src'))
from udpsocket import UDPSocket
from udpdatagram import UDPDatagram
def UDPSocketTestPickleJar_Accept(sock, q):
    conn = sock.Accept(1)
    q.put(conn.sock.getpeername())

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
        s.Send(payload)
        self.assertTrue(s.seq == seq + 1)
        for i in range(0, 1000):
            d = t.Recv()
            if d != None:
                break
        self.assertTrue(d != None)
        s.Close()
        t.Close()
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

    def test_HandshakeAndAccept(self):
        sock = UDPSocket()
        sock.Open()
        sock.Bind(('', 10000))
        q = multiprocessing.Queue()
        p = multiprocessing.Process(target=UDPSocketTestPickleJar_Accept,
                args=(sock, q))
        p.start()
        client = UDPSocket()
        client.Open()
        client.Handshake(('127.0.0.1', 10000), 1)
        client_name = q.get()
        p.join()
        sock.Close()
        self.assertTrue(client.sock.getsockname() == client_name)
        client.Close()

    def test_Pair_1(self):
        p, q = UDPSocket.Pair()
        self.assertTrue(p.sock.getsockname() == q.sock.getpeername())
        self.assertTrue(p.sock.getpeername() == q.sock.getsockname())
        self.assertTrue(p.ttl == UDPSocket.MAX_TIME_TO_LIVE)
        self.assertTrue(q.ttl == UDPSocket.MAX_TIME_TO_LIVE)

