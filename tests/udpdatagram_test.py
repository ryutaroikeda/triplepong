import os
import sys
import unittest
sys.path.append(os.path.abspath('src'))
from udpdatagram import UDPDatagram
class UDPDatagramTest(unittest.TestCase):

    def template_SerializeAndDeserialize(self, seq, ack, ackbits, payload):
        d = UDPDatagram()
        d.seq = seq
        d.ack = ack
        d.ackbits = ackbits
        d.payload = payload
        b = d.Serialize()
        e = UDPDatagram()
        e.Deserialize(b)
        self.assertTrue(d == e)

    def test_eq_1(self):
        d = UDPDatagram()
        self.assertTrue(d == d)

    def test_eq_2(self):
        d = UDPDatagram()
        self.assertTrue(not d == None)

    def test_ne_1(self):
        d = UDPDatagram()
        self.assertTrue(d != None)

    def test_ne_2(self):
        d = UDPDatagram()
        self.assertTrue(not d != d)

    def test_SerializeAndDeserialize(self):
        self.template_SerializeAndDeserialize(0, 0, 0, 
                b'0'*UDPDatagram.MAX_PAYLOAD)
