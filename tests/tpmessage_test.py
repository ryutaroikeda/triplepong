import logging
import os
import select
import socket
import sys
import time
import unittest
sys.path.append(os.path.abspath('src'))
import tplogger
from tpmessage import TPMessage
logger = tplogger.getTPLogger('tpmessage_test.log', logging.DEBUG)
class TPMessageTest(unittest.TestCase):
    def template_SerializeAndDeserialize(self, msg):
        b = msg.Serialize()
        t = TPMessage()
        t.Deserialize(b[4:])
        self.assertTrue(msg == t)

    def test_SerializeAndDeserialize_1(self):
        msg = TPMessage()
        self.template_SerializeAndDeserialize(msg)

    def test_SerializeAndDeserialize_2(self):
        msg = TPMessage()
        msg.timestamp = 1.0
        self.template_SerializeAndDeserialize(msg)
