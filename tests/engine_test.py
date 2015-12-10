import copy
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
sys.path.append(os.path.abspath('tests'))
from mockkeyboard import MockKeyboard
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
        received_keys = e.GetClientEvents([client], 1)
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
        r.SetSize(50)
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
        self.assertTrue(s.frame == 60)
        auth = GameState()
        for i in range(0, 10):
            e.PlayFrame(auth, 0)
        self.assertTrue(auth.frame == 10)
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
        s.Init()
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
        rewound_state = e.RewindAndReplayWithKey(s, evt, r)
        self.assertTrue(rewound_state != None)
        test = GameState()
        test.Init()
        e.PlayFrame(test, flags)
        for i in range(1, 60):
            e.PlayFrame(test, 0)
            pass
        logger.debug("\n{0}\n{1}".format(test, rewound_state))
        test.Diff(rewound_state)
        self.assertTrue(r.states[0].key_flags == flags)
        self.assertTrue(test == rewound_state)

    def test_rewind_with_key2(self):
        '''Test rewind and replay with key over record containing a key.'''
        e = GameEngine()
        s = GameState()
        s.Init()
        r = GameRecord()
        r.SetSize(61)
        for i in range(0, 30):
            r.AddEntry(s, 0)
            e.PlayFrame(s, 0)
            pass
        r.AddEntry(s, GameEvent.EVENT_FLAP_BALL)
        e.PlayFrame(s, GameEvent.EVENT_FLAP_BALL)
        for i in range(0, 29):
            r.AddEntry(s, 0)
            e.PlayFrame(s, 0)
            pass
        evt = GameEvent()
        evt.frame = 10
        evt.keys = GameEvent.EVENT_FLAP_LEFT_PADDLE
        rewound = e.RewindAndReplayWithKey(s, evt, r)
        self.assertTrue(rewound != None)
        test = GameState()
        test.Init()
        for i in range(0, 10):
            e.PlayFrame(test, 0)
            pass
        e.PlayFrame(test, GameEvent.EVENT_FLAP_LEFT_PADDLE)
        for i in range(0, 19):
            e.PlayFrame(test, 0)
            pass
        e.PlayFrame(test, GameEvent.EVENT_FLAP_BALL)
        for i in range(0, 29):
            e.PlayFrame(test, 0)
            pass
        self.assertTrue(test == rewound)
        pass

    def test_run_game(self):
        '''Test consistency of game state between server and client (one 
        event).'''
        ssock, csock = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        svr = EventSocket(ssock)
        client = EventSocket(csock)
        keyboard = MockKeyboard()
        keyboard.inputs = [0]*10 + [1] + [0]*29
        svr_e = GameEngine()
        svr_e.clients = [client]
        svr_s = GameState()
        svr_rec = GameRecord()
        svr_rec.SetSize(40)
        clt_e = GameEngine()
        clt_e.key_cool_down_time = 0
        clt_e.server = svr
        clt_s = GameState()
        clt_rec = GameRecord()
        clt_rec.SetSize(40)
        for i in range(0, 20):
            svr_e.RunFrameAsServer(svr_s, svr_rec)
            pass
        for i in range(0, 20):
            clt_e.RunFrameAsClient(clt_s, clt_rec)
            pass
        # The server should receive event (frame 10) from client and apply
        # rewind and replay.
        svr_e.RunFrameAsServer(svr_s, svr_rec)
        # Compute the client's state had there been no update from the server.
        clt_s_copy = copy.deepcopy(clt_s)
        clt_e.PlayFrame(clt_s_copy, 0)
        # The client should receive state update (frame 20) from the server and 
        # apply rewind and replay.
        clt_e.RunFrameAsClient(clt_s, clt_rec)
        # The states should be consistent.
        self.assertTrue(clt_s == svr_s)
        # Since there was no other input to the server, copy should match.
        self.assertTrue(clt_s_copy == clt_s)

    def test_run_game2(self):
        '''Test consistency of game state between server and client (two
        events).'''
        ssock, csock = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        svr = EventSocket(ssock)
        client = EventSocket(csock)
        keyboard = MockKeyboard()
        keyboard.inputs = [0]*10 + [1] + [0]*9 + [1] + [0]*9
        svr_e = GameEngine()
        svr_e.clients = [client]
        svr_s = GameState()
        svr_rec = GameRecord()
        svr_rec.SetSize(40)
        clt_e = GameEngine()
        clt_e.key_cool_down_time = 0
        clt_e.server = svr
        clt_s = GameState()
        clt_rec = GameRecord()
        clt_rec.SetSize(40)
        for i in range(0, 30):
            svr_e.RunFrameAsServer(svr_s, svr_rec)
            pass
        for i in range(0, 30):
            clt_e.RunFrameAsClient(clt_s, clt_rec)
            pass
        # The server should receive events from client and apply
        # rewind and replay.
        for i in range(0, 20):
            svr_e.RunFrameAsServer(svr_s, svr_rec)
        # Compute the client's state had there been no update from the server.
        clt_s_copy = copy.deepcopy(clt_s)
        for i in range(0, 20):
            clt_e.PlayFrame(clt_s_copy, 0)
        # The client should receive state update (frame 20) from the server and 
        # apply rewind and replay.
        for i in range(0, 20):
            clt_e.RunFrameAsClient(clt_s, clt_rec)
        # The states should be consistent.
        self.assertTrue(clt_s == svr_s)
        # Since there was no other input to the server, copy should match.
        self.assertTrue(clt_s_copy == clt_s)
        pass

