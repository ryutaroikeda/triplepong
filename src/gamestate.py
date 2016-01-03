import logging
import os
import struct
import sys
sys.path.append(os.path.abspath('src'))
from gameobject import GameObject
from eventtype import EventType
import tplogger
logger = tplogger.getTPLogger('gamestate.log', logging.DEBUG)
class GameState:
    '''This class represents the current game state.

    Attributes:
    frame     -- The number of frames since the start of the game.
    key_flags -- The keys pressed in the current frame.
    game_length -- The maximum duration of the game. 
    rounds    -- The number of rounds to play. A round consists of three 
                 rotations.
    round_length -- The duration of a round in frames.
    rotation_length -- The duration of a rotation in frames.

    UDP
    bits            -- The key input of 64 previous frames for each player.
    '''
    ROLE_NONE = 0
    ROLE_LEFT_PADDLE = 1
    ROLE_RIGHT_PADDLE = 2
    ROLE_BALL = 3
    SUBFORMAT = '!hhhhhhhhhQQQQ'
    FORMAT    = '!ihhhhhhhhhQQQQ'
    OBJECT_NONE = 0
    OBJECT_SCREEN = 1
    OBJECT_LEFT_GOAL = 2
    OBJECT_RIGHT_GOAL = 3
    OBJECT_TOP_BALL_WALL = 4
    OBJECT_BOTTOM_BALL_WALL = 5
    OBJECT_TOP_WALL = 6
    OBJECT_BOTTOM_WALL = 7
    OBJECT_BALL = 9
    OBJECT_LEFT_PADDLE = 9
    OBJECT_RIGHT_PADDLE = 10
    def __init__(self):
        '''Create the initial game state.
        '''
        buffer_region = 50
        ball_wall_offset_x = 8
        ball_wall_offset_y = 40
        paddle_offset = 60
        paddle_half_width = 8
        paddle_half_height = 30
        ball_vel = 4
        ball_half_size = 4
        self.event_type = EventType.STATE_UPDATE
        # objects
        self.screen = GameObject()
        self.goal_left = GameObject()
        self.goal_right = GameObject()
        self.ball_wall_top = GameObject()
        self.ball_wall_bottom = GameObject()
        self.paddle_wall_top = GameObject()
        self.paddle_wall_bottom = GameObject()
        self.ball = GameObject()
        self.paddle_left = GameObject()
        self.paddle_right = GameObject()
        #self.objects = [self.screen, self.goal_left, self.goal_right,
        #        self.ball_wall_top, self.ball_wall_bottom,
        #        self.paddle_wall_top, self.paddle_wall_bottom,
        #        self.ball, self.paddle_left, self.paddle_right]
        # The number of players.
        self.player_size = 3
        self.game_length = 120.0
        self.frames_per_sec = 60.0
        self.sec_per_frame = 1 / self.frames_per_sec
        self.rounds = 2
        self.rotation_length = ((self.game_length / self.rounds) * \
                self.frames_per_sec) // self.player_size
        self.round_length = self.rotation_length * self.player_size
        self.screen.half_width = 320
        self.screen.half_height = 240
        self.goal_left.pos_x = - buffer_region
        self.goal_left.pos_y = self.screen.half_height
        self.goal_left.half_width = buffer_region
        self.goal_left.half_height = 100 *  self.screen.half_height
        self.goal_right.pos_x = 2 * self.screen.half_width + buffer_region
        self.goal_right.pos_y = self.screen.half_height
        self.goal_right.half_width = buffer_region
        self.goal_right.half_height = 100 * self.screen.half_height
        self.ball_wall_top.pos_x = self.screen.half_width
        self.ball_wall_top.pos_y = - buffer_region + ball_wall_offset_y
        self.ball_wall_top.half_width = (self.screen.half_width - \
                paddle_offset - paddle_half_width - ball_wall_offset_x)
        self.ball_wall_top.half_height = buffer_region
        self.ball_wall_bottom.pos_x = self.screen.half_width
        self.ball_wall_bottom.pos_y = (2 * self.screen.half_height + \
                buffer_region - ball_wall_offset_y)
        self.ball_wall_bottom.half_width = (self.screen.half_width - \
                paddle_offset - paddle_half_width - ball_wall_offset_x)
        self.ball_wall_bottom.half_height = buffer_region
        self.paddle_wall_top.pos_x = self.screen.half_width
        self.paddle_wall_top.pos_y = - buffer_region
        self.paddle_wall_top.half_width = 2 * self.screen.half_width
        self.paddle_wall_top.half_height = buffer_region
        self.paddle_wall_bottom.pos_x = self.screen.half_width
        self.paddle_wall_bottom.pos_y = (2 * self.screen.half_height + \
                buffer_region)
        self.paddle_wall_bottom.half_width = 2 * self.screen.half_width
        self.paddle_wall_bottom.half_height = buffer_region
        self.ball.pos_x = self.screen.half_width
        self.ball.pos_y = self.screen.half_height
        self.ball.vel_x = -ball_vel
        self.ball.vel_y = 0
        self.ball.half_width = ball_half_size
        self.ball.half_height = ball_half_size
        self.paddle_left.pos_x = paddle_offset
        self.paddle_left.pos_y = 0
        self.paddle_left.vel_x = 0
        self.paddle_left.vel_y = 0
        self.paddle_left.half_width = paddle_half_width
        self.paddle_left.half_height = paddle_half_height
        self.paddle_right.pos_x = 2 * self.screen.half_width - paddle_offset 
        self.paddle_right.pos_y = 0
        self.paddle_right.vel_x = 0
        self.paddle_right.vel_y = 0
        self.paddle_right.half_width = paddle_half_width
        self.paddle_right.half_height = paddle_half_height
        # scores[p] is the score for player p.
        self.scores = [0, 0, 0]
        # roles[p] is the current role of player p.
        self.roles = [GameState.ROLE_LEFT_PADDLE, GameState.ROLE_RIGHT_PADDLE,
                GameState.ROLE_BALL]
        # players[r] is the ID of the player with role r.
        self.players = [0, 0, 1, 2]
        self.frame = 0
        self.key_flags = 0
        self.should_render_score = False
        self.is_ended = False
        self.player_id = 0
        # 64 frames of input history for each player (and flags)
        self.bits = [0, 0, 0, 0]

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        if other == None:
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        '''Override default hash behaviour (which is to return the object ID).
        We do this define equality.'''
        return hash(tuple(sorted(self.__dict__.items())))

    def Diff(self, other):
        a = self.__dict__
        b = other.__dict__
        for key in a:
            if a[key] != b[key]:
                logger.debug('{0}: {1} != {2}'.format(key, a[key], b[key]))
                pass
            pass
        pass

    def GetSize(self):
        return struct.calcsize(GameState.SUBFORMAT)

    def Serialize(self):
        '''Serialize a partial representation of the state.

        The partial representation is sent by the server to clients. It 
        consists of the the frame number and position and velocities of the 
        ball and the paddles. (Only the y component of the paddles is sent). 

        Return value:
        A byte string representation of the partial state.'''
        return struct.pack(GameState.FORMAT,
                EventType.STATE_UPDATE,
                self.ball.pos_x, self.ball.pos_y,
                self.ball.vel_x, self.ball.vel_y,
                self.paddle_left.pos_y, self.paddle_left.vel_y,
                self.paddle_right.pos_y, self.paddle_right.vel_y,
                self.key_flags, self.frame, 
                self.bits[0], self.bits[1], self.bits[2])

    def Deserialize(self, b):
        '''Deserialize a partial representation of the state.'''
        (self.ball.pos_x, self.ball.pos_y,
                self.ball.vel_x, self.ball.vel_y,
                self.paddle_left.pos_y, self.paddle_left.vel_y,
                self.paddle_right.pos_y, self.paddle_right.vel_y,
                self.key_flags, self.frame,
                self.bits[0], self.bits[1], self.bits[2],) = \
                        struct.unpack(GameState.SUBFORMAT, b)

    def Copy(self, other):
        '''Copy this partial state without creating a new instance.
        '''
        other.ball.pos_x = self.ball.pos_x
        other.ball.pos_y = self.ball.pos_y
        other.ball.vel_x = self.ball.vel_x
        other.ball.vel_y = self.ball.vel_y
        other.paddle_left.pos_y = self.paddle_left.pos_y
        other.paddle_left.vel_y = self.paddle_left.vel_y
        other.paddle_right.pos_y = self.paddle_right.pos_y
        other.paddle_right.vel_y = self.paddle_right.vel_y
        other.key_flags = self.key_flags
        other.frame = self.frame
        pass

    def PlayerToObject(self, roles, player_id):
        '''
        Get the object corresponding to a player's role.
        '''
        assert isinstance(roles, list)
        assert isinstance(player_id, int)
        assert 0 <= player_id and player_id < 3
        if roles[player_id] == GameState.ROLE_LEFT_PADDLE:
            return self.paddle_left
        if roles[player_id] == GameState.ROLE_RIGHT_PADDLE:
            return self.paddle_right
        if roles[player_id] == GameState.ROLE_BALL:
            return self.ball
        return None

    def CopyExceptPlayer(self, other, roles, player_id):
        '''
        Copy the state of GameObjects not controlled by player_id into other.
        '''
        assert other != None
        assert isinstance(roles, list)
        assert isinstance(player_id, int)
        assert 0 <= player_id and player_id <= 2
        o = other.PlayerToObject(roles, player_id)
        pos_x = o.pos_x
        pos_y = o.pos_y
        vel_x = o.vel_x
        vel_y = o.vel_y
        self.Copy(other)
        o.pos_x = pos_x
        o.pos_y = pos_y
        o.vel_x = vel_x
        o.vel_y = vel_y
