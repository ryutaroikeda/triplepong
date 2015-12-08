import os
import socket
import sys
import unittest
sys.path.append(os.path.abspath('src'))
from engine import GameEngine
from gamestate import GameState

class GameEngineTest(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass
    def test_send_and_receive_state(self):
        svr, client = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        e = GameEngine()
        s = GameState()
        s.ball.pos_x = 100
        e.SendStateUpdate(s, [client])
        t = e.GetServerEvent(svr)
        self.assertTrue(t.ball.pos_x == s.ball.pos_x)
        pass
    pass
