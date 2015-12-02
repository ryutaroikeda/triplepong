import multiprocessing
import os
import sys
import time
import pygame
sys.path.append(os.path.abspath('src'))
from gameobject import GameObject
from gamestate import GameState
from gameevent import GameEvent
from renderer import Renderer

class GameEngine(object):
    def __init__(self):
        pass

    def GetEvents(self):
        '''Return a list of events to apply.

        Return value:
        The list of events that should be applied to the current frame. Each 
        event is a value defined in GameEvent (see ApplyEvents() and 
        gameevent.py).

        To do: Use EventQueue and move the keyboard event getter elsewhere.
        To do: Allow user to configure key bindings.'''
        evts = []
        # Events should be pumped before calling get_pressed(). These functions 
        # are wrappers for SDL functions intended to be used in this way.
        # See https://www.pygame.org/docs/ref/
        # key.html#comment_pygame_key_get_pressed
        pygame.event.pump()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            evts.append(GameEvent.EVENT_FLAP_LEFT_PADDLE)
            pass
        return evts

    def ApplyGravity(self, s):
        '''Apply gravity to the paddles and the ball

        Arguments:
        s -- the game state'''

        if s.paddle_left.vel_y < 16:
            s.paddle_left.vel_y += 1
            pass
        if s.paddle_right.vel_y < 16:
            s.paddle_right.vel_y += 1
            pass
        if s.ball.vel_y < 16:
            s.ball.vel_y += 1
            pass
        pass

    def ApplyEvents(self, s, evts):
        '''Apply the effect of events to the game state.

        evts should be a list consisting of the following values defined 
        in gameevent.py:
        EVENT_FLAP_NO_OP         -- Do nothing.
        EVENT_FLAP_LEFT_PADDLE
        EVENT_FLAP_RIGHT_PADDLE
        EVENT_FLAP_BALL          -- Update the velocity.

        More events could be defined in the future.

        Arguments:
        s    -- the game state.
        evts -- a list of events to apply.'''

        for e in evts:
            if e == GameEvent.EVENT_FLAP_LEFT_PADDLE:
                s.paddle_left.vel_y = -8
                pass
            if e == GameEvent.EVENT_FLAP_RIGHT_PADDLE:
                s.paddle_right.vel_y = -8
                pass
            if e == GameEvent.EVENT_FLAP_BALL:
                s.ball.vel_y = -4
                pass
            pass
        pass

    def PlayFrame(self, s):
        '''Update the game state by one frame.
        
        Arguments:
            s    -- the state of the game.'''

        # update positions 
        s.ball.pos_x += s.ball.vel_x
        s.ball.pos_y += s.ball.vel_y
        s.paddle_left.pos_y += s.paddle_left.vel_y
        s.paddle_right.pos_y += s.paddle_right.vel_y
        # handle collisions
        if s.paddle_left.IsCollidingWith(s.ball):
            s.paddle_left.AlignRight(s.ball)
            s.ball.vel_x = - s.ball.vel_x
            pass
        if s.paddle_right.IsCollidingWith(s.ball):
            s.paddle_right.AlignLeft(s.ball)
            s.ball.vel_x = - s.ball.vel_x
            pass
        if s.ball.IsCollidingWith(s.ball_wall_top):
            s.ball_wall_top.AlignBottom(s.ball)
            s.ball.vel_y = - s.ball.vel_y
            pass
        if s.ball.IsCollidingWith(s.ball_wall_bottom):
            s.ball_wall_bottom.AlignTop(s.ball)
            s.ball.vel_y = - s.ball.vel_y
            pass
        if s.paddle_left.IsCollidingWith(s.paddle_wall_top):
            s.paddle_wall_top.AlignBottom(s.paddle_left)
            s.paddle_left.vel_y = - s.paddle_left.vel_y
            pass
        if s.paddle_right.IsCollidingWith(s.paddle_wall_top):
            s.paddle_wall_top.AlignBottom(s.paddle_right)
            s.paddle_right.vel_y = - s.paddle_right.vel_y
            pass
        if s.paddle_left.IsCollidingWith(s.paddle_wall_bottom):
            s.paddle_wall_bottom.AlignTop(s.paddle_left)
            s.paddle_left.vel_y = - s.paddle_left.vel_y
            pass
        if s.paddle_right.IsCollidingWith(s.paddle_wall_bottom):
            s.paddle_wall_bottom.AlignTop(s.paddle_right)
            s.paddle_right.vel_y = - s.paddle_right.vel_y
            pass
        if s.ball.IsCollidingWith(s.goal_left):
            s.ball.pos_x = ( s.goal_right.pos_x + s.goal_left.pos_x ) / 2
            s.ball.pos_y = ( s.ball_wall_top.pos_y +
                    s.ball_wall_bottom.pos_y ) / 2
            s.ball.vel_x = -4
            s.ball.vel_y = 0
            s.scores[ s.players[ GameState.ROLE_RIGHT_PADDLE ] ] += 1
            pass
        if s.ball.IsCollidingWith(s.goal_right):
            s.ball.pos_x = ( s.goal_right.pos_x + s.goal_left.pos_x ) / 2
            s.ball.pos_y = ( s.ball_wall_top.pos_y +
                    s.ball_wall_bottom.pos_y ) / 2
            s.ball.vel_x = 4
            s.ball.vel_y = 0
            s.scores[ s.players[ GameState.ROLE_LEFT_PADDLE ] ] += 1
            pass
        pass

    def Run(self):
        s = GameState()
        s.game_length = 9.0
        s.sessionlength = s.game_length / 3
        # the number of rounds (i.e. rotation of roles) per game
        s.rounds = 1
        s.frames_per_sec = 30.0
        s.sec_per_frame = 1 / s.frames_per_sec
        s.screen.half_width = 320
        s.screen.half_height = 240
        buffer_region = 50
        s.goal_left.pos_x = - buffer_region
        s.goal_left.pos_y = s.screen.half_height
        s.goal_left.half_width = buffer_region
        s.goal_left.half_height = 100 *  s.screen.half_height
        s.goal_right.pos_x = 2 * s.screen.half_width + buffer_region
        s.goal_right.pos_y = s.screen.half_height
        s.goal_right.half_width = buffer_region
        s.goal_right.half_height = 100 * s.screen.half_height
        s.ball_wall_top.pos_x = s.screen.half_width
        s.ball_wall_top.pos_y = - buffer_region
        s.ball_wall_top.half_width = s.screen.half_width
        s.ball_wall_top.half_height = buffer_region
        s.ball_wall_bottom.pos_x = s.screen.half_width
        s.ball_wall_bottom.pos_y = 2 * s.screen.half_height +  buffer_region
        s.ball_wall_bottom.half_width = s.screen.half_width
        s.ball_wall_bottom.half_height = buffer_region
        s.paddle_wall_top.pos_x = s.screen.half_width
        s.paddle_wall_top.pos_y = - buffer_region
        s.paddle_wall_top.half_width = 2 * s.screen.half_width
        s.paddle_wall_top.half_height = buffer_region
        s.paddle_wall_bottom.pos_x = s.screen.half_width
        s.paddle_wall_bottom.pos_y = 2 * s.screen.half_height +  buffer_region
        s.paddle_wall_bottom.half_width = 2 * s.screen.half_width
        s.paddle_wall_bottom.half_height = buffer_region
        s.ball.pos_x = s.screen.half_width
        s.ball.pos_y = s.screen.half_height
        s.ball.vel_x = -4
        s.ball.vel_y = 0
        s.ball.half_width = 2
        s.ball.half_height = 2
        s.paddle_left.pos_x = 60
        s.paddle_left.pos_y = 0
        s.paddle_left.vel_x = 0
        s.paddle_left.vel_y = 0
        s.paddle_left.half_width = 10
        s.paddle_left.half_height = 60 
        s.paddle_right.pos_x = 2 * s.screen.half_width - 60
        s.paddle_right.pos_y = 0
        s.paddle_right.vel_x = 0
        s.paddle_right.vel_y = 0
        s.paddle_right.half_width = 10
        s.paddle_right.half_height = 60
        # scores[p] is the score for player p.
        s.scores = [0, 0, 0]
        # roles[p] is the current role of player p.
        s.roles = [GameState.ROLE_LEFT_PADDLE, GameState.ROLE_RIGHT_PADDLE,
                GameState.ROLE_BALL]
        # players[r] is the ID of the player with role r.
        s.players = [0, 1, 2]
        s.start_time = time.time()
        r = Renderer()
        r.Init()
        while True:
            s.frame_start = time.time()
            if s.frame_start - s.start_time >= s.game_length:
                break
            evts = self.GetEvents()
            self.ApplyGravity(s)
            self.ApplyEvents(s, evts)
            self.PlayFrame(s)
            r.RenderAll(s)
            pass
        pass
    pass

if __name__ == '__main__':
    e = GameEngine()
    e.Run()
    pass
