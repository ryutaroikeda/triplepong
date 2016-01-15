import os
import struct
import sys
sys.path.append(os.path.abspath('src'))
from eventtype import EventType

class GameConfig:
    '''This class is used to configure the game. 
    This can be sent as an event using UDPEventSocket.
    Attributes:
    post_game_time -- The number of seconds to run after end of game.
    '''

    FORMAT=   '!ihdhhhhhhhhhhhhhhhhh'
    SUBFORMAT='!hdhhhhhhhhhhhhhhhhh'

    def __init__(self):
        self.event_type = EventType.CONFIGURE
        self.player_size =3
        self.game_length = 120
        self.frames_per_sec = 40
        self.screen_width = 640
        self.screen_height = 480
        self.buffer_region = 50
        self.ball_wall_offset_x = 8
        self.ball_wall_offset_y = 40
        self.paddle_offset = 60
        self.paddle_width = 16
        self.paddle_height = 60
        self.ball_vel = 4
        self.ball_size = 16
        self.rounds = 2
        self.buffer_delay = 2
        self.cool_down = 8
        self.do_interpolate = False
        self.player_id = 0
        self.post_game_time = 30
        # These are not serialized.
        self.do_sync = False
        self.sync_timeout = 2.0
        self.sync_rate = 15
        self.buffer_size = 64
        self.start_time = 0.0
        self.resend = 5

    def __repr__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        if other == None:
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

    def GetSize(self):
        return struct.calcsize(self.SUBFORMAT)

    def Serialize(self):
        return struct.pack(self.FORMAT, self.event_type,
                self.player_size, self.game_length, self.frames_per_sec,
                self.screen_width, self.screen_height, self.buffer_region,
                self.ball_wall_offset_x, self.ball_wall_offset_y,
                self.paddle_offset, self.paddle_width, self.paddle_height,
                self.ball_vel, self.ball_size, self.rounds, 
                self.buffer_delay, self.cool_down,  self.do_interpolate,
                self.player_id, self.post_game_time)

    def Deserialize(self, b):
        (self.player_size, self.game_length, self.frames_per_sec,
                self.screen_width, self.screen_height, self.buffer_region,
                self.ball_wall_offset_x, self.ball_wall_offset_y,
                self.paddle_offset, self.paddle_width, self.paddle_height,
                self.ball_vel, self.ball_size, self.rounds, 
                self.buffer_delay, self.cool_down, self.do_interpolate,
                self.player_id, self.post_game_time) = \
                        struct.unpack(self.SUBFORMAT, b)

    def ApplyState(self, s):
        '''Apply the configuration to a game state.
        Argument:
        s -- The game state.
        '''
        buffer_region = self.buffer_region
        ball_wall_offset_x = self.ball_wall_offset_x
        ball_wall_offset_y = self.ball_wall_offset_y
        paddle_offset = self.paddle_offset
        paddle_half_width = self.paddle_width // 2
        paddle_half_height = self.paddle_height // 2
        ball_vel = self.ball_vel
        ball_half_size = self.ball_size // 2
        s.player_size = self.player_size
        s.game_length = self.game_length
        s.frames_per_sec = self.frames_per_sec
        s.rounds = self.rounds
        if s.rounds > 0:
            s.rotation_length = int((s.game_length / s.rounds) * \
                    s.frames_per_sec) 
            if s.player_size > 0:
                s.rotation_length //= s.player_size
        else:
            s.rotation_length = 0
        s.round_length = s.rotation_length * s.player_size
        s.screen.half_width = self.screen_width // 2
        s.screen.half_height = self.screen_height // 2
        s.goal_left.pos_x = - buffer_region
        s.goal_left.pos_y = s.screen.half_height
        s.goal_left.half_width = buffer_region
        s.goal_left.half_height = 100 *  s.screen.half_height
        s.goal_right.pos_x = 2 * s.screen.half_width + buffer_region
        s.goal_right.pos_y = s.screen.half_height
        s.goal_right.half_width = buffer_region
        s.goal_right.half_height = 100 * s.screen.half_height
        s.ball_wall_top.pos_x = s.screen.half_width
        s.ball_wall_top.pos_y = - buffer_region + ball_wall_offset_y
        s.ball_wall_top.half_width = (s.screen.half_width - \
                paddle_offset - paddle_half_width - ball_wall_offset_x)
        s.ball_wall_top.half_height = buffer_region
        s.ball_wall_bottom.pos_x = s.screen.half_width
        s.ball_wall_bottom.pos_y = (2 * s.screen.half_height + \
                buffer_region - ball_wall_offset_y)
        s.ball_wall_bottom.half_width = (s.screen.half_width - \
                paddle_offset - paddle_half_width - ball_wall_offset_x)
        s.ball_wall_bottom.half_height = buffer_region
        s.paddle_wall_top.pos_x = s.screen.half_width
        s.paddle_wall_top.pos_y = - buffer_region
        s.paddle_wall_top.half_width = 2 * s.screen.half_width
        s.paddle_wall_top.half_height = buffer_region
        s.paddle_wall_bottom.pos_x = s.screen.half_width
        s.paddle_wall_bottom.pos_y = (2 * s.screen.half_height + \
                buffer_region)
        s.paddle_wall_bottom.half_width = 2 * s.screen.half_width
        s.paddle_wall_bottom.half_height = buffer_region
        s.ball.pos_x = s.screen.half_width
        s.ball.pos_y = s.screen.half_height
        s.ball.vel_x = -ball_vel
        s.ball.vel_y = 0
        s.ball.half_width = ball_half_size
        s.ball.half_height = ball_half_size
        s.paddle_left.pos_x = paddle_offset
        s.paddle_left.pos_y = 0
        s.paddle_left.vel_x = 0
        s.paddle_left.vel_y = 0
        s.paddle_left.half_width = paddle_half_width
        s.paddle_left.half_height = paddle_half_height
        s.paddle_right.pos_x = 2 * s.screen.half_width - paddle_offset 
        s.paddle_right.pos_y = 0
        s.paddle_right.vel_x = 0
        s.paddle_right.vel_y = 0
        s.paddle_right.half_width = paddle_half_width
        s.paddle_right.half_height = paddle_half_height
    
    def ApplyRenderer(self, r):
        '''Apply the configuration to a renderer.
        Argument:
        r -- The renderer to configre.
        '''
        r.do_interpolate = self.do_interpolate
        self.ApplyState(r.state)

    def Apply(self, e):
        '''Apply the configuration to a game engine.
        Argument:
        e -- The game engine to configure.
        '''
        e.buffer_delay = self.buffer_delay
        e.key_cool_down_time = self.cool_down
        e.key_buffer = [0]*e.buffer_delay
        e.player_id = self.player_id
        e.key_bindings = [-1, -1, -1]
        e.key_bindings[e.player_id] = 32
        e.start_time = self.start_time
        e.post_game_time = self.post_game_time
        e.rec.SetSize(self.buffer_size)
        self.ApplyState(e.state)
