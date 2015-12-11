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

    def test_GetKeyboardEvents(self):
        '''Test keyboard input is converted to game events.
        '''
        e = GameEngine()
        e.key_cool_down_time = 0
        s = GameState()
        k = MockKeyboard()
        k.inputs = [0, 1]*3
        e.keyboard = k
        player_ids = [0, 1, 2]
        expected_keys = [[GameEvent.EVENT_NO_OP,
                GameEvent.EVENT_FLAP_LEFT_PADDLE],
                [GameEvent.EVENT_NO_OP,
                GameEvent.EVENT_FLAP_RIGHT_PADDLE],
                [GameEvent.EVENT_NO_OP,
                GameEvent.EVENT_FLAP_BALL]]
        for i in range(0, 3):
            e.player_id = player_ids[i]
            for j in range(0, 2):
                key_flag = e.GetKeyboardEvents(s)
                self.assertTrue(key_flag == expected_keys[i][j])
                pass
            pass
        pass

    def test_GetServerEvent(self):
        '''Test server event when server is None.
        '''
        e = GameEngine()
        evt = e.GetServerEvent(None)
        self.assertTrue(evt == None)
        pass

    def test_GetClientEvents(self):
        '''Test empty clients case.
        To do: test unread.
        '''
        e = GameEngine()
        current_frame = 0
        clients = []
        evts = e.GetClientEvents(clients, current_frame)
        self.assertTrue(evts == [])
        pass


    def test_send_and_receive_state(self):
        svrsock, csock = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        svr = EventSocket(svrsock)
        client = EventSocket(csock)
        e = GameEngine()
        s = GameState()
        s.ball.pos_x = 100
        e.SendStateUpdate([client], s)
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
        received_keys = e.GetClientEvents([client], 1)
        self.assertTrue(received_keys[0].keys == keys)
        pass

    def test_PlayFrame(self):
        '''Test frame count and key_flags in PlayFrame.
        '''
        e = GameEngine()
        s = GameState()
        frame = s.frame
        s.key_flags = GameEvent.EVENT_FLAP_LEFT_PADDLE
        e.PlayFrame(s, s.key_flags)
        self.assertTrue(s.frame == frame + 1)
        self.assertTrue(s.key_flags == 0)
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
        if test != rewound_state:
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
        if test != rewound:
            logger.debug('\n{0}\n{1}'.format(test, rewound))
        self.assertTrue(test == rewound)
        pass

    def test_rewind_with_state3(self):
        '''Test that rewind with no new information is consistent with normal
        play.
        '''
        e = GameEngine()
        keyboard = MockKeyboard()
        keyboard.inputs = [0]*10 + [1] + [0]*40
        e.keyboard = keyboard
        e.key_cool_down_time = 0
        s = GameState()
        rec = GameRecord()
        rec.SetSize(50)
        for i in range(0, 20):
            e.RunFrameAsClient(s, rec)
            pass
        # state at frame 20
        auth = GameState()
        s.Copy(auth)
        for i in range(0, 10):
            e.RunFrameAsClient(s, rec)
            pass
        # The state without rewind at frame 30.
        self.assertTrue(s.frame == 30)
        s_copy = GameState()
        s.Copy(s_copy)
        auth = e.RewindAndReplayWithState(auth, s.frame, rec)
        self.assertTrue(auth != None)
        self.assertTrue(auth == s_copy)

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
        rewound_state = e.RewindAndReplayWithKey(s, evt, r)
        self.assertTrue(rewound_state != None)
        test = GameState()
        e.PlayFrame(test, flags)
        for i in range(1, 60):
            e.PlayFrame(test, 0)
            pass
        if test != rewound_state:
            logger.debug("\n{0}\n{1}".format(test, rewound_state))
        test.Diff(rewound_state)
        self.assertTrue(r.states[0].key_flags == flags)
        self.assertTrue(test == rewound_state)

    def test_rewind_with_key2(self):
        '''Test rewind and replay with key over record containing a key.'''
        e = GameEngine()
        s = GameState()
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
        svr_e.is_server = True
        svr_e.clients = [client]
        svr_s = GameState()
        svr_rec = GameRecord()
        svr_rec.SetSize(40)
        clt_e = GameEngine()
        clt_e.is_client = True
        clt_e.key_cool_down_time = 0
        clt_e.keyboard = keyboard
        clt_e.server = svr
        clt_s = GameState()
        clt_rec = GameRecord()
        clt_rec.SetSize(40)
        for i in range(0, 20):
            svr_e.RunFrameAsServer(svr_s, svr_rec)
            pass
        for i in range(0, 21):
            clt_e.RunFrameAsClient(clt_s, clt_rec)
            pass
        self.assertTrue(clt_s.frame == 21)
        # The server should receive event (frame 10) from client and apply
        # rewind and replay.
        for i in range(0, 2):
            svr_e.RunFrameAsServer(svr_s, svr_rec)
        # Compute the client's state had there been no update from the server.
        clt_s_copy = copy.deepcopy(clt_s)
        clt_rec_copy = copy.deepcopy(clt_rec)
        # Run without the server
        clt_e.server = None
        clt_e.RunFrameAsClient(clt_s_copy, clt_rec_copy)
        self.assertTrue(clt_s_copy.frame == 22)
        # Get the server back
        clt_e.server = svr
        # The client should receive state update (frame 20) from the server and 
        # apply rewind and replay.
        clt_e.RunFrameAsClient(clt_s, clt_rec)
        self.assertTrue(clt_s.frame == 22)
        # The states should be consistent.
        if clt_s != svr_s:
            logger.debug('\n{0}\n{1}'.format(clt_s, svr_s))
            clt_s.Diff(svr_s)
        self.assertTrue(clt_s == svr_s)
        # Since there was no other input to the server, copy should match.
        # If they don't, the client would see a hitch.
        if clt_s != clt_s_copy:
            logger.debug('\n{0}\n{1}'.format(clt_s, clt_s_copy))
            clt_s.Diff(clt_s_copy)
        self.assertTrue(clt_s_copy == clt_s)
        ssock.close()
        csock.close()

    @unittest.skip('auth jump should not happen')
    def test_run_game2(self):
        '''Test consistency of game state between server and client (two
        events).'''
        ssock, csock = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        svr = EventSocket(ssock)
        client = EventSocket(csock)
        keyboard = MockKeyboard()
        keyboard.inputs = [0]*10 + [1] + [0]*9 + [1] + [0]*9
        svr_e = GameEngine()
        svr_e.is_server = True
        svr_e.clients = [client]
        svr_s = GameState()
        svr_rec = GameRecord()
        svr_rec.SetSize(60)
        clt_e = GameEngine()
        clt_e.is_client = True
        clt_e.key_cool_down_time = 0
        clt_e.server = svr
        clt_e.keyboard = keyboard
        clt_s = GameState()
        clt_rec = GameRecord()
        clt_rec.SetSize(60)
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
        clt_s_copy.server = None
        for i in range(0, 20):
            clt_e.PlayFrame(clt_s_copy, 0)
        # The client should receive state update (frame 20) from the server and 
        # apply rewind and replay.
        for i in range(0, 20):
            clt_e.RunFrameAsClient(clt_s, clt_rec)
        if clt_s != svr_s:
            logger.debug('\n{0}\n{1}'.format(clt_s, svr_s))
        # The states should be consistent.
        self.assertTrue(clt_s == svr_s)
        # Since there was no other input to the server, copy should match.
        self.assertTrue(clt_s_copy == clt_s)
        pass

    @unittest.skip('to do')
    def test_server_two_clients(self):
        '''To do:
        Test that one client sees the input of another via the server.'''
        ssock1, csock1 = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        ssock2, csock2 = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        svr1 = EventSocket(ssock1)
        client1 = EventSocket(csock1)
        svr2 = EventSocket(ssock2)
        client2 = EventSocket(csock2)
        svr_e = GameEngine()
        svr_e.clients = [client1, client2]
        svr_s = GameState()
        svr_rec = GameRecord()
        svr_rec.SetSize(60)
        keyboard = MockKeyboard()
        keyboard.inputs = [0]*10 + [1] + [0]*9 + [1] + [0]*9
        clt1_e = GameEngine()
        clt1_e.server = svr1
        clt1_e.key_cool_down_time = 0
        clt1_e.keyboard = keyboard
        


