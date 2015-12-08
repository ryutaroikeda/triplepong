import os
import socket
import sys
import time
import unittest
sys.path.append(os.path.abspath('src'))
from engine import GameEngine
from eventsocket import EventSocket
from gamestate import GameState

class GameEngineTest(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass
    def test_send_and_receive_state(self):
        svrsock, csock = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        svr = EventSocket(svrsock)
        client = EventSocket(csock)
        e = GameEngine()
        s = GameState()
        s.ball.pos_x = 100
        e.SendStateUpdate([client], s)
        time.sleep(.5)
        t = e.GetServerEvent(svr)
        self.assertTrue(t.ball.pos_x == s.ball.pos_x)
        pass
    pass
