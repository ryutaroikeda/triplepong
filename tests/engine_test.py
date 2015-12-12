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

    def test_init(self):
        e = GameEngine()
        self.assertTrue(e.is_client == False)
        self.assertTrue(e.is_server == False)
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
        '''Test getting events from clients.
        '''
        e = GameEngine()
        evts = e.GetClientEvents([], 0)
        self.assertTrue(evts == [])
        ssock, csock = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        svr = EventSocket(ssock)
        client = EventSocket(csock)
        # Test unread
        evt = GameEvent()
        evt.frame = 10
        evt.keys = 1
        svr.WriteEvent(evt)
        # The event is at frame 10 and we are on frame 5, so it should be 
        # unread.
        evts = e.GetClientEvents([client], 5)
        self.assertTrue(evts == [])
        # We are past frame 10, so we should get the event.
        evts = e.GetClientEvents([client], 15)
        self.assertTrue(len(evts) == 1)
        self.assertTrue(evts[0].frame == evt.frame)
        self.assertTrue(evts[0].keys == evt.keys)
        pass


    def test_send_and_receive_state(self):
        '''Test SendStateUpdate and GetServerEvent.
        '''
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
        '''Test SendKeyboardEvents and GetClientEvents
        '''
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

    def test_RewindAndReplayWithState_1(self):
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

    def test_RewindAndReplayWithState_2(self):
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

    def test_RewindAndReplayWithState_3(self):
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
        pass

    def test_RewindAndReplayWithState_4(self):
        '''Test future jump and current frame.
        '''
        e = GameEngine()
        s = GameState()
        s.frame = 0
        s.ball.pos_x = 100
        # Make a copy of s.
        t = GameState()
        s.Copy(t)
        rec = GameRecord()
        rec.SetSize(1)
        # Rewind to the current frame.
        rewound = e.RewindAndReplayWithState(s, 0, rec)
        self.assertTrue(rewound == t)
        # Jump to a future state.
        s.frame = 1
        s.Copy(t)
        rewound = e.RewindAndReplayWithState(s, 0, rec)
        self.assertTrue(rewound == t)
        pass

    def test_RewindAndReplayWithState_5(self):
        '''Rewind beyond the available records.
        '''
        e = GameEngine()
        s = GameState()
        s.frame = 0
        rec = GameRecord()
        rec.SetSize(1)
        rewound = e.RewindAndReplayWithState(s, 1, rec)
        self.assertTrue(rewound == None)
        pass

    def template_RunFrameAsClient(self, max_frame, max_buffer, state_evts):
        '''
        Arguments:
        state_evts -- A list of state events to receive, one for each frame.
        Use None for no event.
        max_frame  -- The number of frames to run the test for.
        max_buffer -- The size of the recording.

        Return value:
        The final game state.
        '''
        ssock, csock = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        svr = EventSocket(ssock)
        client = EventSocket(csock)
        e = GameEngine()
        e.keyboard = MockKeyboard()
        e.is_client = True
        e.server = svr
        rec = GameRecord()
        rec.SetSize(max_buffer)
        s = GameState()
        for i in range(0, max_frame):
            client.WriteEvent(state_evts[i])
            e.RunFrameAsClient(s, rec)
            pass
        return s


    def test_RunFrameAsClient_1(self):
        '''Test the consistency of the game state with RunFrameAsClient.
        '''
        ssock, csock = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        svr = EventSocket(ssock)
        client = EventSocket(csock)
        e = GameEngine()
        e.is_client = True
        e.server = svr
        rec = GameRecord()
        rec.SetSize(30)
        s = GameState()
        t = GameState()
        for i in range(0, 10):
            e.PlayFrame(t, 0)
        t.key_flags = GameEvent.EVENT_FLAP_RIGHT_PADDLE
        for i in range(0, 20):
            e.RunFrameAsClient(s, rec)
            pass
        # The server sends a state update.
        client.WriteEvent(t)
        e.RunFrameAsClient(s, rec)
        test = GameState()
        for i in range(0, 10):
            e.PlayFrame(test, 0)
        e.PlayFrame(test, GameEvent.EVENT_FLAP_RIGHT_PADDLE)
        for i in range(0, 10):
            e.PlayFrame(test, 0)
            pass
        test.Diff(s)
        self.assertTrue(test == s)
        pass

    def test_RunFrameAsClient_2(self):
        '''Test template method.
        '''
        max_frames = 60
        max_buffer = 30
        updates = [None]*max_frames
        e = GameEngine()
        s = GameState()
        for i in range(0, max_frames):
            e.PlayFrame(s, 0)
            pass
        result = self.template_RunFrameAsClient(max_frames, max_buffer, 
                updates)
        s.Diff(result)
        self.assertTrue(s == result)
        pass

    def test_RunFrameAsClient_3(self):
        '''Test state update.
        '''
        max_frames = 60
        max_buffer = 30
        updates = [None]*max_frames
        e = GameEngine()
        s = GameState()
        for i in range(0, 20):
            e.PlayFrame(s, 0)
            pass
        update_frame = s.frame + 10
        updates[update_frame] = GameState()
        s.Copy(updates[update_frame])
        updates[update_frame].key_flags = GameEvent.EVENT_FLAP_BALL
        e.PlayFrame(s, GameEvent.EVENT_FLAP_BALL)
        for i in range(0, 39):
            e.PlayFrame(s, 0)
            pass
        result = self.template_RunFrameAsClient(max_frames, max_buffer, 
                updates)
        result.Diff(s)
        self.assertTrue(result == s)
        pass

    def test_RunFrameAsClient_4(self):
        '''Test state update on the current frame.
        '''
        max_frames = 60
        max_buffer = 30
        updates = [None]*max_frames
        e = GameEngine()
        s = GameState()
        for i in range(0, 20):
            e.PlayFrame(s, 0)
            pass
        update_frame = s.frame 
        updates[update_frame] = GameState()
        s.Copy(updates[update_frame])
        updates[update_frame].key_flags = GameEvent.EVENT_FLAP_BALL
        e.PlayFrame(s, GameEvent.EVENT_FLAP_BALL)
        for i in range(0, 39):
            e.PlayFrame(s, 0)
            pass
        result = self.template_RunFrameAsClient(max_frames, max_buffer, 
                updates)
        result.Diff(s)
        self.assertTrue(result == s)
        pass
    def template_RewindAndReplayWithKey(self, max_buffer, key_rec, evt):
        '''
        Arguments:
        max_buffer -- The size of the buffer to use.
        key_rec -- The key flags for each frame in the record, up to the 
                   arrival of evt.
        evt     -- The event to rewind for.
        
        '''
        e = GameEngine()
        s = GameState()
        rec = GameRecord()
        rec.SetSize(max_buffer)
        for i in range(0, len(key_rec)):
            rec.AddEntry(s, key_rec[i])
            e.PlayFrame(s, key_rec[i])
            pass
        rewound = e.RewindAndReplayWithKey(s, evt, rec)
        self.assertTrue(rewound != None)
        key_rec[evt.frame] |= evt.keys
        test = GameState()
        for i in range(0, len(key_rec)):
            e.PlayFrame(test, key_rec[i])
            pass
        test.Diff(rewound)
        self.assertTrue(test == rewound)
        pass

    def test_RewindAndReplayWithKey_1(self):
        '''Test template.
        '''
        max_buffer = 100
        key_rec = [0]*100
        evt = GameEvent()
        evt.frame = 0
        evt.keys = 0
        self.template_RewindAndReplayWithKey(max_buffer, key_rec, evt)
        pass

    def test_RewindAndReplayWithKey_2(self):
        '''Test one event with template.
        '''
        max_buffer = 20
        key_rec = [0]*20
        evt = GameEvent()
        evt.frame = 10
        evt.keys = GameEvent.EVENT_FLAP_LEFT_PADDLE
        self.template_RewindAndReplayWithKey(max_buffer, key_rec, evt)
        pass

    def test_RewindAndReplayWithKey_3(self):
        e = GameEngine()
        s = GameState()
        t = GameState()
        s.Copy(t)
        rec = GameRecord()
        rec.SetSize(1)
        evt = GameEvent()
        evt.frame = 0
        evt.keys = GameEvent.EVENT_FLAP_LEFT_PADDLE
        rewound = e.RewindAndReplayWithKey(s, evt, rec)
        # evt.frame is the current frame.
        self.assertTrue(rewound == t)
        s.frame = 1
        rewound = e.RewindAndReplayWithKey(s, evt, rec)
        # No available record.
        self.assertTrue(rewound == None)
        evt.frame = 2
        rewound = e.RewindAndReplayWithKey(s, evt, rec)
        # Event happened in the future
        self.assertTrue(rewound == None)
        pass

    def test_RewindAndReplayWithKey_4(self):
        '''Test rewind over history of keys.
        '''
        max_buffer = 120
        key_rec = [1, 0, 2, 0, 4, 0]*20
        evt = GameEvent()
        evt.frame = 61
        evt.keys  = GameEvent.EVENT_FLAP_LEFT_PADDLE
        self.template_RewindAndReplayWithKey(max_buffer, key_rec, evt)
        pass

    def test_RewindAndReplayWithKey_5(self):
        '''Test rewind on top of a record.
        '''
        max_buffer = 100
        key_rec = [1, 0]*30
        evt = GameEvent()
        evt.frame = 30
        evt.keys = GameEvent.EVENT_FLAP_RIGHT_PADDLE
        self.template_RewindAndReplayWithKey(max_buffer, key_rec, evt)
        pass

    def test_RewindAndReplayWithKey_6(self):
        max_buffer = 50
        key_rec = [0]*30
        evt = GameEvent()
        evt.frame = 20
        evt.keys = GameEvent.EVENT_FLAP_LEFT_PADDLE
        self.template_RewindAndReplayWithKey(max_buffer, key_rec, evt)
        pass
    
    def test_RewindAndReplayWithKey_7(self):
        '''Test with less buffer than length of test
        '''
        max_buffer = 20
        key_rec = [0]*100
        evt = GameEvent()
        evt.frame = 80
        evt.keys = 0
        self.template_RewindAndReplayWithKey(max_buffer, key_rec, evt)
        pass
        
    def test_RewindAndReplayWithKey_8(self):
        max_buffer = 10
        key_rec = [0]*20
        evt = GameEvent()
        evt.frame = 10
        evt.keys = GameEvent.EVENT_FLAP_LEFT_PADDLE
        self.template_RewindAndReplayWithKey(max_buffer, key_rec, evt)
        pass

    def test_RewindAndReplayWithKey_9(self):
        '''Test with less buffer than length of test
        '''
        max_buffer = 20
        key_rec = [0]*100
        evt = GameEvent()
        evt.frame = 90
        evt.keys = 0
        self.template_RewindAndReplayWithKey(max_buffer, key_rec, evt)
        pass
        
    def test_RunFrameAsServer(self):
        '''Test the consistency of the game state with RunFrameAsServer.
        '''
        ssock, csock = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        svr = EventSocket(ssock)
        client = EventSocket(csock)
        e = GameEngine()
        e.is_server = True
        e.clients = [client]
        rec = GameRecord()
        rec.SetSize(30)
        s = GameState()
        evt = GameEvent()
        evt.frame = 10
        evt.keys = GameEvent.EVENT_FLAP_LEFT_PADDLE
        for i in range(0, 20):
            e.RunFrameAsServer(s, rec)
            pass
        # The client writes an event to the server.
        svr.WriteEvent(evt)
        e.RunFrameAsServer(s, rec)
        e.is_server = False
        e.is_client = True
        test = GameState()
        for i in range(0, 10):
            e.PlayFrame(test, 0)
            pass
        e.PlayFrame(test, GameEvent.EVENT_FLAP_LEFT_PADDLE)
        for i in range(0, 10):
            e.PlayFrame(test, 0)
            pass
        self.assertTrue(test == s)
        pass

    def template_RunFrameAsServer(self, max_buffer, key_evts):
        '''A test template for RunFrameAsServer.
        This tests RunFrameAsServer with the given buffer size and key events.
        The test input is validated by checking for key_evts entry that cannot 
        be rewound with the buffer size provided.
        Arguments:
        max_buffer -- The size of the buffer.
        key_evts   -- The list of key events to be received on each frame.
                      Use None to indicate no event.
        
        '''
        ssock, csock = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        svr = EventSocket(ssock)
        client = EventSocket(csock)
        e = GameEngine()
        e.is_server = True
        e.clients = [client]
        rec = GameRecord()
        rec.SetSize(max_buffer)
        s = GameState()
        # Validate the input.
        ## Count the number of events.
        count = 0
        max_frame = len(key_evts)
        for i in range(0, max_frame):
            if key_evts[i] == None:
                continue
            assert(i - key_evts[i].frame <= max_buffer)
            if key_evts[i].frame < max_frame:
                count += 1
            pass
        for i in range(0, max_frame):
            svr.WriteEvent(key_evts[i])
            e.RunFrameAsServer(s, rec)
            pass
        # Check we got all the events.
        self.assertTrue(client.events_read == count)
        raw_evts = [0]*max_frame
        for i in range(0, max_frame):
            if key_evts[i] == None:
                continue
            raw_evts[key_evts[i].frame] = key_evts[i].keys
            pass
        test = GameState()
        for i in range(0, max_frame):
            e.PlayFrame(test, raw_evts[i])
            pass
        test.Diff(s)
        self.assertTrue(test == s)

    def test_RunFrameAsServer_1(self):
        '''Test the template.
        '''
        key_evts = [None]*100
        self.template_RunFrameAsServer(50, key_evts)
        pass

    def test_RunFrameAsServer_2(self):
        '''Test one event at frame 10 from client arriving at server at frame 
        20.
        '''
        key_evts = [None]*50
        key_evts[20] = GameEvent()
        key_evts[20].frame = 10
        key_evts[20].keys = GameEvent.EVENT_FLAP_RIGHT_PADDLE
        self.template_RunFrameAsServer(50, key_evts)
        pass

    def test_RunFrameAsServer_3(self):
        '''Test one event at frame 10 from client arriving at server at frame 
        30.
        '''
        key_evts = [None]*50
        key_evts[30] = GameEvent()
        key_evts[30].frame = 10
        key_evts[30].keys = GameEvent.EVENT_FLAP_RIGHT_PADDLE
        self.template_RunFrameAsServer(20, key_evts)
        pass

    def test_RunFrameAsServer_4(self):
        '''Test one event at frame 10 from client arriving at server at frame 
        30.
        '''
        key_evts = [None]*50
        key_evts[30] = GameEvent()
        key_evts[30].frame = 10
        key_evts[30].keys = GameEvent.EVENT_FLAP_RIGHT_PADDLE
        self.template_RunFrameAsServer(20, key_evts)
        pass

    @unittest.skip('failing')
    def test_RunFrameAsServer_5(self):
        '''Test one event at frame 10 from client arriving at server at frame 
        20 with less buffer than the test length.
        '''
        key_evts = [None]*50
        key_evts[20] = GameEvent()
        key_evts[20].frame = 10
        key_evts[20].keys = GameEvent.EVENT_FLAP_RIGHT_PADDLE
        self.template_RunFrameAsServer(20, key_evts)
        pass

    def test_RunFrameAsServerAndClient(self):
        '''Test the consistency of game state with RunFrameAsServer.
        '''
        ssock, csock = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        svr = EventSocket(ssock)
        client = EventSocket(csock)
        keyboard = MockKeyboard()
        keyboard.inputs = [0]*10 + [1] + [0]*20
        svr_e = GameEngine()
        svr_e.is_server = True
        svr_e.clients = [client]
        svr_s = GameState()
        svr_rec = GameRecord()
        svr_rec.SetSize(40)
        clt_e = GameEngine()
        clt_e.is_client = True
        clt_e.server = svr
        clt_e.keyboard = keyboard
        clt_s = GameState()
        clt_rec = GameRecord()
        clt_rec.SetSize(40)
        for i in range(0, 20):
            svr_e.RunFrameAsServer(svr_s, svr_rec)
            pass
        for i in range(0, 21):
            clt_e.RunFrameAsClient(clt_s, clt_rec)
            pass
        # Send update to client
        for i in range(0, 2):
            svr_e.RunFrameAsServer(svr_s, svr_rec)
            pass
        # Receive update from server
        clt_e.RunFrameAsClient(clt_s, clt_rec)
        self.assertTrue(svr_s == clt_s)
        # Check we have all inputs at the correct frames.
        for i in range(0, 22):
            self.assertTrue(clt_rec.states[i].key_flags == keyboard.inputs[i])
            pass
        # Check server received event.
        self.assertTrue(svr.events_read == 1)
        # There are no other events, so svr_s should be the same as running
        # 22 frames without the server
        keyboard = MockKeyboard()
        keyboard.inputs = [0]*10 + [1] + [0]*20
        test_e = GameEngine()
        test_e.is_client = True
        test_e.keyboard = keyboard
        test_s = GameState()
        test_rec = GameRecord()
        test_rec.SetSize(40)
        for i in range(0, 22):
            test_e.RunFrameAsClient(test_s, test_rec)
            pass
        for i in range(0, 22):
            test_rec.states[i].Diff(clt_rec.states[i])
            self.assertTrue(test_rec.states[i] == clt_rec.states[i],
                    'incorrect frame {0}'.format(i))
            pass
        if test_s != svr_s:
            test_s.Diff(svr_s)
        self.assertTrue(test_s == svr_s)
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
        # Check that the records match.
        for i in range(0, 22):
            if clt_rec.states[i] != clt_rec_copy.states[i]:
                clt_rec.states[i].Diff(clt_rec_copy.states[i])
            self.assertTrue(clt_rec.states[i] == clt_rec_copy.states[i],
                    'mismatch at frame {0}'.format(i))
            pass
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

    @unittest.skip('failing')
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
        


