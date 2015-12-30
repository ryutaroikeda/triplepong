import os
import sys
import unittest
sys.path.append(os.path.abspath('src'))
from engine import GameEngine
from gameconfig import GameConfig
from gamestate import GameState
class GameConfigTest(unittest.TestCase):
    def test_eq_1(self):
        conf = GameConfig()
        self.assertTrue(conf == conf)

    def test_eq_2(self):
        conf = GameConfig()
        conf2 = GameConfig()
        self.assertTrue(conf == conf2)

    def test_eq_3(self):
        conf = GameConfig()
        conf.game_length = 51
        conf2 = GameConfig()
        conf2.game_length = 51
        self.assertTrue(conf == conf2)

    def test_ne_1(self):
        conf = GameConfig()
        conf.game_length = 413
        conf2 = GameConfig()
        conf2.game_length = 32
        self.assertTrue(conf != conf2)

    def test_SerializeAndDeserialize(self):
        conf = GameConfig()
        conf.player_size = 5
        conf.game_length = 40
        conf.frames_per_sec = 130
        conf.screen_width = 1024
        conf.screen_height = 756
        conf.buffer_region = 89
        conf.ball_wall_offset_x = 9357
        conf.ball_wall_offset_y = 932
        conf.paddle_width = 32
        conf.paddle_height = 50
        conf.ball_vel = 3
        conf.ball_size = 100
        conf.rounds = 8
        conf.buffer_delay = 1
        conf.player_id = 2
        # Ignore the event type bytes.
        b = conf.Serialize()[4:]
        test = GameConfig()
        test.Deserialize(b)
        self.assertTrue(conf == test, msg='{0} != {1}'.format(conf, test))

    def test_Apply(self):
        conf = GameConfig()
        conf.frames_per_sec = 120
        conf.game_length = 60
        conf.rounds = 2
        conf.screen_width = 1024
        conf.screen_height = 756
        conf.paddle_width = 32
        conf.paddle_height = 50
        conf.ball_size = 100
        conf.player_id = 2
        conf.cool_down = 5
        e = GameEngine()
        conf.Apply(e)
        self.assertTrue(e.player_id == conf.player_id)
        self.assertTrue(e.key_cool_down_time == conf.cool_down)
        s = e.state
        self.assertTrue(s.frames_per_sec == conf.frames_per_sec)
        self.assertTrue(s.game_length == conf.game_length)
        self.assertTrue(s.rounds == conf.rounds)
        self.assertTrue(s.rotation_length == conf.frames_per_sec * 10)
        self.assertTrue(s.round_length == conf.frames_per_sec * 30)
        self.assertTrue(s.screen.half_width == conf.screen_width // 2)
        self.assertTrue(s.screen.half_height == conf.screen_height // 2)
        self.assertTrue(s.paddle_left.half_width == conf.paddle_width // 2)
        self.assertTrue(s.paddle_right.half_height == \
                conf.paddle_height // 2)
        self.assertTrue(s.ball.half_width == conf.ball_size // 2)
