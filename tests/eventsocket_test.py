import os
import socket
import sys
import time
import unittest
sys.path.append(os.path.abspath('src'))
from eventsocket import EventSocket
from gameevent import GameEvent
from gamestate import GameState
from endgameevent import EndGameEvent
class EventSocketTest(unittest.TestCase):
    def template_ReadAndWriteEvent(self, evt):
        ssock, csock = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        svr = EventSocket(ssock)
        client = EventSocket(csock)
        svr.WriteEvent(evt)
        start_time = time.time()
        timeout = 2
        received_evt = None
        while time.time() - start_time <= timeout:
            received_evt = client.ReadEvent()
            if not received_evt == None:
                break
        self.assertTrue(received_evt == evt)

    def test_GameEvent(self):
        evt = GameEvent()
        evt.keys = GameEvent.EVENT_FLAP_LEFT_PADDLE
        self.template_ReadAndWriteEvent(evt)

    def test_StateUpdate(self):
        evt = GameState()
        evt.ball.pos_x = 100
        evt.paddle_left.vel_y = 345
        evt.paddle_right.pos_y = -894
        self.template_ReadAndWriteEvent(evt)

    def test_EndGameEvent(self):
        evt = EndGameEvent()
        evt.score_0 = 2
        evt.score_1 = 31
        evt.score_2 = -4
        self.template_ReadAndWriteEvent(evt)

    def test_read_and_write_state_update(self):
        ssock, csock = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        svr = EventSocket(ssock)
        client = EventSocket(csock)
        evt = GameState()
        evt.ball.pos_x = 100
        svr.WriteEvent(evt)
        start_time = time.time()
        timeout = 2
        while time.time() - start_time <= timeout:
            self.received_evt = client.ReadEvent()
            if not self.received_evt == None:
                break
        self.assertTrue(self.received_evt.ball.pos_x == evt.ball.pos_x)
    pass

        


