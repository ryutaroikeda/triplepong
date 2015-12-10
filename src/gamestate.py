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
    key_flags -- The keys pressed in the current frame.'''
    ROLE_NONE = 0
    ROLE_LEFT_PADDLE = 1
    ROLE_RIGHT_PADDLE = 2
    ROLE_BALL = 3
    SUBFORMAT = '!iiiiiiiiiL'
    FORMAT    = '!iiiiiiiiiiL'
    def __init__(self):
        ##
        ## Game configuration
        ## These states do not need to be sent during the game
        ##
        self.frame = 0
        # the duration of the game in seconds
        self.game_length = 0.0
        # the number of rounds (i.e. rotation of roles) per game
        self.rounds = 1
        self.frames_per_sec = 30.0
        self.sec_per_frame = 1 / self.frames_per_sec
        self.screen = GameObject()
        self.goal_left = GameObject()
        self.goal_right = GameObject()
        self.ball_wall_top = GameObject()
        self.ball_wall_bottom = GameObject()
        self.paddle_wall_top = GameObject()
        self.paddle_wall_bottom = GameObject()
        # scores[p] is the score for player p.
        self.scores = [0, 0, 0]
        # roles[p] is the current role of player p.
        self.roles = [GameState.ROLE_LEFT_PADDLE, 
                GameState.ROLE_RIGHT_PADDLE, GameState.ROLE_BALL]
        # players[r] is the player of role r.
        self.players = [0, 1, 2]
        self.key_flags = 0
        ##
        ## Game states
        ## Parts of these are sent by the server to each client
        ##
        self.ball = GameObject()
        self.paddle_left = GameObject()
        self.paddle_right = GameObject()
        pass

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
        for key in b:
            if a[key] != b[key]:
                logger.debug('{0}: {1} != {2}'.format(key, a[key], b[key]))
        for key in a:
            if a[key] != b[key]:
                logger.debug('{0}: {1} != {2}'.format(key, a[key], b[key]))
                pass
            pass
        pass

    def GetSize():
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
                self.key_flags,
                self.frame)
    def Deserialize(self, b):
        '''Deserialize a partial representation of the state.'''
        (self.ball.pos_x, self.ball.pos_y,
                self.ball.vel_x, self.ball.vel_y,
                self.paddle_left.pos_y, self.paddle_left.vel_y,
                self.paddle_right.pos_y, self.paddle_right.vel_y,
                self.key_flags,
                self.frame,) = struct.unpack(GameState.SUBFORMAT, b)
        pass
    def ApplyUpdate(self, update):
        '''Updates the state of the game with update, a partial game state.

        The partial game state is that obtained from Serialize() and 
        Deserialize().

        Argument:
        update -- The partial game state to apply.'''
        self.ball.pos_x = update.ball.pos_x
        self.ball.pos_y = update.ball.pos_y
        self.ball.vel_x = update.ball.vel_x
        self.ball.vel_y = update.ball.vel_y
        self.paddle_left.pos_y = update.paddle_left.pos_y
        self.paddle_left.vel_y = update.paddle_left.vel_y
        self.paddle_right.pos_y = update.paddle_right.pos_y
        self.paddle_right.vel_y = update.paddle_right.vel_y
        self.key_flags |= update.key_flags
        self.frame = update.frame
        pass
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

    def Init(self):
        '''Create the initial game state.

        To do: Add arguments to configure the game.

        Return value:
        The initial game state.'''
        buffer_region = 50
        ball_wall_offset_x = 8
        ball_wall_offset_y = 40
        paddle_offset = 60
        paddle_half_width = 8
        paddle_half_height = 30
        # The number of players.
        self.player_size = 3
        self.game_length = 60.0
        # the number of rounds (i.e. full rotation of roles) per game
        self.rounds = 1
        self.round_length = self.game_length / self.rounds
        self.rotation_length = self.round_length / self.player_size
        self.frames_per_sec = 60.0
        self.sec_per_frame = 1 / self.frames_per_sec
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
        self.ball.vel_x = -4
        self.ball.vel_y = 0
        self.ball.half_width = 2
        self.ball.half_height = 2
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
        self.start_time = 0
        pass
    pass
