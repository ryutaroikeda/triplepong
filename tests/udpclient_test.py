import os
import sys
import unittest
sys.path.append(os.path.abspath('src'))
from engine import GameEngine
from gamerecord import GameRecord
from gamestate import GameState
from udpclient import UDPClient
from udpeventsocket import UDPEventSocket
from udpsocket import UDPSocket
class UDPClientTest(unittest.TestCase):
    def template_ApplyStateUpdate(self, histories, update):
        c = UDPClient()
        e = GameEngine()
        s = GameState()
        size = 64
        rec = GameRecord()
        rec.SetSize(size)
        c.ApplyStateUpdate(e, s, rec, histories, update, size)
        self.assertTrue(s.frame == max(s.frame, update.frame))

    @unittest.skip('')
    def test_ApplyStateUpdate_1(self):
        u = GameState()
        self.template_ApplyStateUpdate([0,0,0],u)
