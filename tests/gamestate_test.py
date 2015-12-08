import os
import sys
import unittest
from gamestate import GameState

class GameStateTest(unittest.TestCase):
    def test_Serialize_and_Deserialize(self):
        s = GameState()
        s.ball.pos_x = 100
        s.ball.pos_y = -50
        s.ball.vel_x = -43
        s.ball.vel_y = 6
        s.paddle_left.pos_y = 90
        s.paddle_left.vel_y = 4
        s.paddle_right.pos_y = 2
        s.paddle_right.vel_y = 87
        s.frame = 112734590
        # Ignore the EventType header.
        b = s.Serialize()[4:]
        t = GameState()
        t.Deserialize(b)
        self.assertTrue(t.ball.pos_x == s.ball.pos_x)
        self.assertTrue(t.ball.pos_y == s.ball.pos_y)
        self.assertTrue(t.ball.vel_x == s.ball.vel_x)
        self.assertTrue(t.ball.vel_y == s.ball.vel_y)
        self.assertTrue(t.paddle_left.pos_y == s.paddle_left.pos_y)
        self.assertTrue(t.paddle_left.vel_y == s.paddle_left.vel_y)
        self.assertTrue(t.paddle_right.pos_y == s.paddle_right.pos_y)
        self.assertTrue(t.paddle_right.vel_y == s.paddle_right.vel_y)
        self.assertTrue(t.frame == s.frame)
        pass


