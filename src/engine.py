import os
import sys
import time
sys.path.append(os.path.abspath('src'))
from gamestate import GameObject
from gamestate import GameState
from renderer import Renderer
# def min(x, y):
#     if x < y:
#         return x
#     else: 
#         return y
#     pass
# def max(x, y):
#     if x > y:
#         return x
#     else:
#         return y
#     pass
# def vec2minus(x, y):
#     return (x[0]-y[0], x[1]-y[1])
# def vec2cross(x, y):
#     return x[0] * y[1] - x[1] * y[0]
# class TPObject(object):
#     def __init__(self):
#         self.posx = 0
#         self.posy = 0
#         self.velx = 0
#         self.vely = 0
#         self.width = 0
#         self.height = 0
#         pass
#     def didcollidewith(self, other):
#         if self.velx >= 0 and self.vely >= 0:
#             p = (self.posx, self.posy)
#             r = (self.velx + self.width, self.vely + self.height)
#         else if self.velx >= 0 and self.vely < 0:
#             p = (self.posx, self.posy + self.height)
#             r = (self.velx + self.width, self.vely)
#         else if self.velx < 0 and self.vely >= 0:
#             p = (self.posx + self.width, self.posy)
#             r = (self.velx, self.vely + self.height)
#         else if self.velx < 0 and self.vely < 0:
#             p = (self.posx + self.width, self.posy + self.height)
#             r = (self.velx, self.vely)
#             pass
#         if other.velx >= 0 and other.vely >= 0:
#             q = (other.posx, other.posy)
#             s = (other.velx + other.width, other.vely + other.height)
#         else if other.velx >= 0 and other.vely < 0:
#             q = (other.posx, other.posy + other.height)
#             s = (other.velx + other.width, other.vely)
#         else if other.velx < 0 and other.vely >= 0:
#             q = (other.posx + other.width, other.posy)
#             s = (other.velx, other.vely + other.height)
#         else if other.velx < 0 and other.vely < 0:
#             q = (other.posx + other.width, other.posy + other.height)
#             s = (other.velx, other.vely)
#             pass
#         qmp = vec2minus(q, p)
#         rxs = vec2cross(r, s)
#         qmpxs = vec2cross(qmp, s)
#         qmpxr = vec2cross(qmp, r)
#         if rxs == 0:
#             if qmpxs == 0:
#                 # collinear; this shouldn't happen in this game
#                 pass
#             pass
#         # check if starts-to-ends cross
#         return False
#     pass

class GameEngine(object):
    def __init__(self):
        pass
    def PlayFrame(self, s, evts):
        '''Update the game state by one frame.
        
        Arguments:
            s    -- the state of the game.
            evts -- a list of events to apply'''

        # handle events
        
        # update positions 
        s.ball.pos_x += s.ball.vel_x
        s.ball.pos_y += s.ball.vel_y
        s.paddle_left.pos_y = s.paddle_left.vel_y
        s.paddle_right.pos_y = s.paddle_right.vel_y
        # handle collisions
        if s.paddle_left.IsCollidingWith(s.ball):
            s.ball.pos_x = s.paddle_left.pos_x + s.paddle_left.half_width
            s.ball.vel_x = - s.ball.vel_x
            pass
        if s.paddle_right.IsCollidingWith(s.ball):
            s.ball.pos_x = s.paddlerightx - s.paddle_right.half_width
            s.ball.vel_x = - s.ball.vel_x
            pass
        if s.ball.IsCollidingWith(s.ball_wall_top):
            s.ball.pos_y = s.ball_wall_top.pos_y
            s.ball.vel_y = - s.ball.vel_y
            pass
        if s.ball.IsCollidingWith(s.ball_wall_bottom):
            s.ball.pos_y = s.ball_wall_bottom.pos_y
            s.ball.vel_y = - s.ball.vel_y
            pass
        if s.paddle_left.IsCollidingWith(s.paddle_wall_top):
            s.paddle_left.pos_y = s.paddle_wall_top.pos_y
            s.paddle_left.vel_y = - s.paddle_left.vel_y
            pass
        if s.paddle_right.IsCollidingWith(s.paddle_wall_top):
            s.paddle_right.pos_y = s.paddle_wall_top.pos_y
            s.paddle_right.vel_y = - s.paddle_right.vel_y
            pass
        if s.paddle_left.IsCollidingWith(s.paddle_wall_bottom):
            s.paddle_left.pos_y = s.paddle_wall_bottom.pos_y
            s.paddle_left.vel_y = - s.paddle_left.vel_y
            pass
        if s.paddle_right.IsCollidingWith(s.paddle_wall_bottom):
            s.paddle_right.pos_y = s.paddle_wall_bottom.pos_y
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
        s.paddle_left.half_height = 120
        s.paddle_right.pos_x = 2 * s.screen.half_width - 60
        s.paddle_right.pos_y = 0
        s.paddle_right.vel_x = 0
        s.paddle_right.vel_y = 0
        s.paddle_right.half_width = 10
        s.paddle_right.half_height = 120
        # scores[p] is the score for player p.
        s.scores = [0, 0, 0]
        # roles[p] is the current role of player p.
        s.roles = [GameState.ROLE_LEFT_PADDLE, GameState.ROLE_RIGHT_PADDLE,
                GameState.ROLE_BALL]
        # players[r] is the player of role r.
        s.players = [0, 1, 2]
        s.start_time = time.time()
        r = Renderer()
        r.Init()
        while True:
            s.frame_start = time.time()
            if s.frame_start - s.start_time >= s.game_length:
                break
            self.PlayFrame(s)
            r.RenderAll(s)
            pass
        pass
    pass

if __name__ == '__main__':
    e = GameEngine()
    e.Run()
    pass