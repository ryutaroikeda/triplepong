import os
import sys
import unittest
from gamestate import GameState
from gameobject import GameObject

class GameStateTest(unittest.TestCase):
    def template_PlayerToObject(self, s, player_id, expected_object):
        roles = [GameState.ROLE_LEFT_PADDLE,
                GameState.ROLE_RIGHT_PADDLE,
                GameState.ROLE_BALL]
        o = s.PlayerToObject(roles, player_id)
        self.assertTrue(o == expected_object)


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
        s.key_flags = 3
        s.frame = 112734590
        s.keybits = 1 << 63
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
        self.assertTrue(t.key_flags == s.key_flags)
        self.assertTrue(t.frame == s.frame)
        pass

    def test_eq(self):
        s = GameState()
        s.ball.vel_x = 100
        s.roles[0] = GameState.ROLE_BALL
        s.paddle_left = GameObject()
        s.paddle_left.pos_x = 99
        s.players = [3,4,5]
        t = GameState()
        t.ball.vel_x = 100
        t.roles[0] = GameState.ROLE_BALL
        t.paddle_left = GameObject()
        t.paddle_left.pos_x = 99
        t.players = [3,4,5]
        self.assertTrue(s == t)

    def test_ne(self):
        s = GameState()
        s.ball.vel_x = 100
        t = GameState()
        t.ball.vel_x = 200
        self.assertTrue(s != t)
        pass

    def test_Copy(self):
        s = GameState()
        u = GameState()
        u.ball.pos_x = 100
        u.ball.pos_y = 200
        u.ball.vel_x = 300
        u.ball.vel_y = 400
        u.paddle_left.pos_y = -100
        u.paddle_left.vel_y = -200
        u.paddle_right.pos_y = -300
        u.paddle_right.vel_y = -400
        u.frame = 30
        u.key_flags = 300
        u.Copy(s)
        self.assertTrue(s.ball.pos_x == u.ball.pos_x)
        self.assertTrue(s.ball.pos_y == u.ball.pos_y)
        self.assertTrue(s.ball.vel_x == u.ball.vel_x)
        self.assertTrue(s.ball.vel_y == u.ball.vel_y)
        self.assertTrue(s.paddle_left.pos_y == u.paddle_left.pos_y)
        self.assertTrue(s.paddle_left.vel_y == u.paddle_left.vel_y)
        self.assertTrue(s.paddle_right.vel_y == u.paddle_right.vel_y)
        self.assertTrue(s.paddle_right.pos_y == u.paddle_right.pos_y)
        self.assertTrue(s.frame == u.frame)
        self.assertTrue(s.key_flags == u.key_flags)
        pass
    pass
        
    def test_PlayerToObject_1(self):
        s = GameState()
        self.template_PlayerToObject(s, 0, s.paddle_left)

    def test_PlayerToObject_2(self):
        s = GameState()
        self.template_PlayerToObject(s, 1, s.paddle_right)

    def test_PlayerToObject_3(self):
        s = GameState()
        self.template_PlayerToObject(s, 2, s.ball)

    def test_CopyExceptPlayer_1(self):
        s = GameState()
        roles = [GameState.ROLE_LEFT_PADDLE,
                GameState.ROLE_RIGHT_PADDLE,
                GameState.ROLE_BALL]
        s.paddle_left.pos_y = 500
        s.paddle_right.vel_y = 1000
        s.ball.vel_x = 2000
        t = GameState()
        t.paddle_left.pos_y = -500
        t.paddle_right.vel_y = -1000
        t.ball.vel_x = -2000
        s.CopyExceptPlayer(t, roles, 0)
        self.assertTrue(t.paddle_left.pos_y == -500)
        self.assertTrue(t.paddle_right.vel_y == 1000)
        self.assertTrue(t.ball.vel_x == 2000)
