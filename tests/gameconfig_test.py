import os
import sys
import unittest
sys.path.append(os.path.abspath('src'))
from gameconfig import GameConfig
from gamestate import GameState
class GameConfigTest(unittest.TestCase):
    def test_Apply(self):
        conf = GameConfig()
        conf.frame_rate = 120
        conf.game_length = 60
        conf.rounds = 2
        conf.screen_width = 1024
        conf.screen_height = 756
        conf.paddle_width = 32
        conf.paddle_height = 50
        conf.ball_size = 100
        s = GameState()
        conf.Apply(s)
        self.assertTrue(s.frames_per_sec == conf.frame_rate)
        self.assertTrue(s.game_length == conf.game_length)
        self.assertTrue(s.rounds == conf.rounds)
        self.assertTrue(s.rotation_length == conf.frame_rate * 10)
        self.assertTrue(s.round_length == conf.frame_rate * 30)
        self.assertTrue(s.screen.half_width == conf.screen_width // 2)
        self.assertTrue(s.screen.half_height == conf.screen_height // 2)
        self.assertTrue(s.paddle_left.half_width == conf.paddle_width // 2)
        self.assertTrue(s.paddle_right.half_height == \
                conf.paddle_height // 2)
        self.assertTrue(s.ball.half_width == conf.ball_size // 2)
