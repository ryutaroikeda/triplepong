import os
import struct
import sys
sys.path.append(os.path.abspath('src'))
from gameobject import GameObject
from eventtype import EventType

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
        self.paddle_left.pos_y = update.paddle_left.pos_y
        self.paddle_right.pos_y = update.paddle_right.pos_y
        self.paddle_right.vel_y = update.paddle_right.vel_y
        self.key_flags |= update.key_flags
        self.frame = update.frame
        pass
    pass
