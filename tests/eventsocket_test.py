import os
import socket
import sys
import time
import unittest
sys.path.append(os.path.abspath('src'))
from eventsocket import EventSocket
from gameevent import GameEvent
from gamestate import GameState
class EventSocketTest(unittest.TestCase):
    def test_read_and_write(self):
        serversock, clientsock = socket.socketpair(socket.AF_UNIX,
                socket.SOCK_STREAM)
        svr = EventSocket(serversock)
        client = EventSocket(clientsock)
        evt = GameEvent()
        evt.keys.append(GameEvent.EVENT_FLAP_LEFT_PADDLE)
        svr.WriteEvent(evt)
        received_evt = client.ReadEvent()
        self.assertTrue(received_evt.keys[0] == \
                GameEvent.EVENT_FLAP_LEFT_PADDLE)
        pass
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


