import os
import sys
import unittest
sys.path.append(os.path.abspath('src'))
from endgameevent import EndGameEvent
from gameconfig import GameConfig
from gameevent import GameEvent
from gamestate import GameState
from tpmessage import TPMessage
from udpeventsocket import UDPEventSocket
from udpsocket import UDPSocket

class UDPEventSocketTest(unittest.TestCase):
    def template_ReadAndWriteEvent(self, evt):
        s, t = UDPSocket.Pair()
        e = UDPEventSocket(s)
        f = UDPEventSocket(t)
        for i in range(0, 20):
            e.WriteEvent(evt)
        for i in range(0, 20):
            received = f.ReadEvent()
            if received != None:
                break
        s.Close()
        t.Close()
        self.assertTrue(evt == received)
    
    def test_ReadAndWriteEvent_None(self):
        self.template_ReadAndWriteEvent(None)

    def test_ReadAndWriteEvent_Keyboard_1(self):
        evt = GameEvent()
        self.template_ReadAndWriteEvent(evt)

    def test_ReadAndWriteEvent_Keyboard_2(self):
        evt = GameEvent()
        evt.keys = 1
        evt.frame = 1000
        self.template_ReadAndWriteEvent(evt)

    def test_ReadAndWriteEvent_State_1(self):
        evt = GameState()
        self.template_ReadAndWriteEvent(evt)

    def test_ReadAndWriteEvent_State_2(self):
        evt = GameState()
        evt.frame = 100
        evt.ball.pos_x = 3
        evt.ball.pos_y = 6
        evt.paddle_left.pos_y = 5
        evt.paddle_left.vel_y = -9
        evt.paddle_right.pos_y = -19
        evt.paddle_right.vel_y = 54
        evt.key_flags = 4
        self.template_ReadAndWriteEvent(evt)

    def test_ReadAndWriteEvent_EndGame_1(self):
        evt = EndGameEvent()
        self.template_ReadAndWriteEvent(evt)

    def test_ReadAndWriteEvent_EndGame_2(self):
        evt = EndGameEvent()
        evt.score_0 = 3
        evt.score_1 = 484
        evt.score_2 = 3478
        self.template_ReadAndWriteEvent(evt)

    def test_ReadAndWriteEvent_Config_1(self):
        evt = GameConfig()
        self.template_ReadAndWriteEvent(evt)

    def test_ReadAndWriteEvent_Handshake_1(self):
        evt = TPMessage()
        self.template_ReadAndWriteEvent(evt)

    def test_ReadAndWriteEvent_Handshake_2(self):
        evt = TPMessage()
        evt.method = 4
        self.template_ReadAndWriteEvent(evt)



