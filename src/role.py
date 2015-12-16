class Role:
    '''A class for representing a role.
    Attributes:
    role   -- The flag for the role.
    player -- A reference to the player with this role.
    '''
    NONE = 0
    LEFT_PADDLE = 1
    RIGHT_PADDLE = 2
    BALL = 3
    ROLES = [NONE, LEFT_PADDLE, RIGHT_PADDLE, BALL]
    def __init__(self):
        self.role = 0
        self.player = None
