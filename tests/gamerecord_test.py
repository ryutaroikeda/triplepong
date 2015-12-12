import os
import sys
import unittest
sys.path.append(os.path.abspath('src'))
from gamestate import GameState
from gamerecord import GameRecord
from gameevent import GameEvent

class GameRecordTest(unittest.TestCase):
    def test_SetSize(self):
        rec = GameRecord()
        size = 10
        rec.SetSize(size)
        self.assertTrue(rec.size == size)
        self.assertTrue(rec.available == 0)
        self.assertTrue(rec.idx == 0)
        pass

    def test_AddEntry(self):
        rec = GameRecord()
        s = GameState()
        s.ball.pos_x = 100
        rec.SetSize(1)
        rec.AddEntry(s, 0)
        self.assertTrue(rec.idx == 0)
        self.assertTrue(rec.available == 1)
        self.assertTrue(rec.states[0].ball.pos_x == s.ball.pos_x)
        # The record should be a distinct copy of the state.
        s.ball.pos_x = 200
        self.assertTrue(rec.states[0].ball.pos_x != s.ball.pos_x)
        # The record should cycle around.
        rec.AddEntry(s, 0)
        self.assertTrue(rec.states[0].ball.pos_x == s.ball.pos_x)
        pass

    def template_ApplyEvent(self, max_buffer, available, current_frame, 
            evt_frame, keys, result):
        '''
        Arguments:
        max_buffer -- The size of the record.
        available -- The number of frames to make available in the record.
        current_frame -- The current frame.
        evt_frame      -- The frame of the event.
        keys       -- The keys from the event.
        result     -- The expected result of ApplyEvent.
        '''
        assert(available <= max_buffer)
        rec = GameRecord()
        rec.SetSize(max_buffer)
        s = GameState()
        for i in range(0, available):
            rec.AddEntry(s, 0)
            pass
        evt = GameEvent()
        evt.frame = evt_frame
        evt.keys = keys
        r = rec.ApplyEvent(current_frame, evt)
        self.assertTrue(r == result)
        idx = (rec.idx - (current_frame - evt_frame)) % rec.size
        if result == 0:
            self.assertTrue(rec.states[idx].key_flags == evt.keys)
        pass

    def test_ApplyEvent_1(self):
        '''Ignore event in the future.
        '''
        self.template_ApplyEvent(10, 10, 10, 20, 0, -1)
        pass

    def test_ApplyEvent_2(self):
        '''Ignore event when record is unavailable.
        '''
        self.template_ApplyEvent(20, 10, 30, 11, 1, -1)
        pass

    def test_ApplyEvent_3(self):
        '''Apply event.
        '''
        self.template_ApplyEvent(20, 10, 32, 22, 1, 0)
        pass
    pass
