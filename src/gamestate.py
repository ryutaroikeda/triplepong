class GameObject:
    '''A class for representing the objects in the game.'''
    def __init__(self):
        self.pos_x = 0
        self.pos_y = 0
        self.vel_x = 0
        self.vel_y = 0
        self.half_width = 0
        self.half_height = 0
        pass
    def IsCollidingWith(self, other):
        '''Checks for a collision.

        Checks if the object self overlaps with object other. Objects 
        sharing a border are overlapping.
        Argument:
        other -- a GameObject.
        Return value:
        Return 1 if self and other are overlapping and 0 otherwise.'''
        
        if self.pos_x < other.pos_x:
            if self.pos_x + self.half_width < other.pos_x - other.half_width:
                return False
            pass
        else:
            if other.pos_x + other.half_width < self.pos_x - self.half_width:
                return False
            pass
        if self.pos_y < other.pos_y:
            if self.pos_y + self.half_height < other.pos_y - other.half_height:
                return False
            pass
        else:
            if other.pos_y + other.half_height < self.pos_y - self.half_height:
                return False
            pass
        return True
    pass

class GameState:
    ROLE_PADDLE_LEFT = 0
    ROLE_PADDLE_RIGHT = 1
    ROLE_BALL = 2
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
        self.roles = [GameState.ROLE_PADDLE_LEFT, 
                GameState.ROLE_PADDLE_RIGHT, GameState.ROLE_BALL]
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
    pass
