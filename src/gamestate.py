class GameObject:
    def __init__(self):
        self.pos_x = 0
        self.pos_y = 0
        self.vel_x = 0
        self.vel_y = 0
        self.half_width = 0
        self.half_height = 0
        pass
    def IsCollidingWith(self, other):
        # if self.pos_x 
        return False
    pass
class GameState:
    self.ROLE_LEFT_PADDLE = 0
    self.ROLE_RIGHT_PADDLE = 1
    self.ROLE_BALL = 2
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
        self.paddle_wall_top = GameOjbect()
        self.paddle_wall_bottom = GameObject()
        # scores[p] is the score for player p.
        self.scores = [0, 0, 0]
        # roles[p] is the current role of player p.
        self.roles = [self.ROLE_LEFT_PADDLE, self.ROLE_RIGHT_PADDLE,
                self.ROLE_BALL]
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
