import logging
import os
import socket
import sys
import time
import unittest
sys.path.append(os.path.abspath('src'))
from engine import GameEngine
from engine import GameRecord
from eventsocket import EventSocket
from gamestate import GameState
from gameevent import GameEvent
import tplogger
logger = tplogger.getTPLogger('engine_test.log', logging.DEBUG)
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
        time.sleep(.1)
        t = e.GetServerEvent(svr)
        self.assertTrue(t.ball.pos_x == s.ball.pos_x)
        pass
    def test_send_and_receive_key(self):
        ssock, csock = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        svr = EventSocket(ssock)
        client = EventSocket(csock)
        e = GameEngine()
        s = GameState()
        keys = GameEvent.EVENT_FLAP_LEFT_PADDLE
        e.SendKeyboardEvents(svr, s, keys)
        time.sleep(.1)
        received_keys = e.GetClientEvents([client])
        self.assertTrue(received_keys[0].keys == keys)
        pass
    def test_rewind_with_state_1(self):
        e = GameEngine()
        s = GameState()
        r = GameRecord()
        r.SetSize(60)
        for i in range(0, 60):
            r.AddEntry(s, 0)
            e.PlayFrame(s, 0)
            pass
        auth = GameState()
        auth.key_flags = GameEvent.EVENT_FLAP_LEFT_PADDLE
        rewound_state = e.RewindAndReplayWithState(auth, s.frame, r)
        self.assertTrue(rewound_state != None)
        test = GameState()
        e.PlayFrame(test, GameEvent.EVENT_FLAP_LEFT_PADDLE)
        for i in range(1, 60):
            e.PlayFrame(test, 0)
        logger.debug("\n{0}\n{1}".format(test, rewound_state))
        self.assertTrue(test == rewound_state)

    def test_rewind_with_state_2(self):
        '''Test rewinding and replaying on top of recorded key events.'''
        e = GameEngine()
        s = GameState()
        r = GameRecord()
        r.SetSize(70)
        for i in range(0, 30):
            r.AddEntry(s, 0)
            e.PlayFrame(s, 0)
            pass
        r.AddEntry(s, GameEvent.EVENT_FLAP_RIGHT_PADDLE)
        e.PlayFrame(s, GameEvent.EVENT_FLAP_RIGHT_PADDLE)
        for i in range(0, 29):
            r.AddEntry(s, 0)
            e.PlayFrame(s, 0)
            pass
        self.assertTrue(r.idx == 60)
        self.assertTrue(s.frame == 60)
        auth = GameState()
        auth.frame = 10
        auth.key_flags = GameEvent.EVENT_FLAP_BALL
        rewound = e.RewindAndReplayWithState(auth, s.frame, r)
        self.assertTrue(r.states[10].key_flags == GameEvent.EVENT_FLAP_BALL)
        self.assertTrue(r.states[30].key_flags == \
                GameEvent.EVENT_FLAP_RIGHT_PADDLE)
        self.assertTrue(rewound != None)
        test = GameState()
        for i in range(0, 10):
            e.PlayFrame(test, 0)
            pass
        self.assertTrue(test.frame == 10)
        e.PlayFrame(test, GameEvent.EVENT_FLAP_BALL)
        for i in range(0, 19):
            e.PlayFrame(test, 0)
            pass
        self.assertTrue(test.frame == 30)
        e.PlayFrame(test, GameEvent.EVENT_FLAP_RIGHT_PADDLE)
        for i in range(0, 29):
            e.PlayFrame(test, 0)
            pass
        self.assertTrue(test.frame == 60)
        logger.debug('\n{0}\n{1}'.format(test, rewound))
        self.assertTrue(test == rewound)
    
    def test_rewind_with_key(self):
        e = GameEngine()
        s = GameState()
        r = GameRecord()
        r.SetSize(61)
        for i in range(0, 60):
            r.AddEntry(s, 0)
            e.PlayFrame(s, 0)
            pass
        self.assertTrue(r.available == 60)
        evt = GameEvent()
        flags = GameEvent.EVENT_FLAP_LEFT_PADDLE | GameEvent.EVENT_FLAP_BALL
        evt.frame = 0
        evt.keys = flags
        rewound_state = e.RewindAndReplayWithKey(s.frame, evt, r)
        self.assertTrue(rewound_state != None)
        test = GameState()
        e.PlayFrame(test, flags)
        for i in range(1, 60):
            e.PlayFrame(test, 0)
            pass
        logger.debug("\n{0}\n{1}".format(test, rewound_state))
        test.Diff(rewound_state)
        self.assertTrue(r.states[0].key_flags == flags)
        self.assertTrue(test == rewound_state)

    def test_rewind_with_key2(self):
        # to do: replay key on top of other keys
        pass
