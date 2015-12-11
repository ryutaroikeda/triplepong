import os
import sys
import unittest
sys.path.append(os.path.abspath('src'))
from gamerecord import GameRecord

class GameRecordTest:
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
        self.assertTrue(rec.idx == 1)
        self.assertTrue(rec.available == 1)
        self.assertTrue(rec.states[0].ball.pos_x == s.ball.pos_x)
        # The record should be a distinct copy of the state.
        s.ball.pos_x = 200
        self.assertTrue(rec.state[0].ball.pos_x != s.ball.pos_x)
        # The record should cycle around.
        rec.AddEntry(s, 0)
        self.assertTrue(rec.state[0].ball.pos_x == s.ball.pos_x)
        pass

    pass
