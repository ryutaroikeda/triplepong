import os
import select
import socket
import sys
import unittest
sys.path.append(os.path.abspath('src'))
from tpmessage import TPMessage
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
        pid = os.fork()
        if pid == 0:
            server = socket.socket()
            server.bind((socket.gethostname(), 8080))
            server.listen(1)
            # wait for client to call connect()
            select.select([server],[],[],1)
            (conn, _) = server.accept()
            b = conn.recv(4096)
            conn.sendall(b)
            conn.close()
            server.close()
            return
        client = socket.socket()
        while True:
            try:
                client.connect((socket.gethostname(), 8080))
                break
            except:
                pass
            pass
        m = TPMessage()
        m.method = TPMessage.METHOD_ASKREADY
        b1 = m.pack()
        client.sendall(b1)
        b2 = client.recv(4096)
        client.close()
        n = TPMessage()
        n.unpack(b2)
        self.assertTrue(n.method == TPMessage.METHOD_ASKREADY)
        pass
    pass

