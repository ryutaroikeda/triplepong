import os
import sys
sys.path.append(os.path.abspath('src'))
from gameobject import GameObject

class GameState:
    ROLE_NONE = 0
    ROLE_LEFT_PADDLE = 1
    ROLE_RIGHT_PADDLE = 2
    ROLE_BALL = 3
    def __init__(self):
        ##
        ## Game configuration
        ## These states do not need to be sent during the game
        ##
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
        ##
        ## Game states
        ## Parts of these are sent by the server to each client
        ##
        self.ball = GameObject()
        self.paddle_left = GameObject()
        self.paddle_right = GameObject()
        pass
    def Update(self, update):
        '''Update the game state. '''
        pass
    pass
