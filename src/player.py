class Player:
    '''A class for representing the player.
    Attributes:
    key            -- The key to press for generating a game event.
    last_key_frame -- The frame of the last key event.
    role           -- A reference to a Role object.
    entity         -- The game object controlled by the player.
    color          -- The color of the player controlled object.
    '''
    def __init__(self):
        self.is_active = False
        self.key = 0
        self.last_key_frame = 0
        self.role = None
        self.entity = None
        self.color = (0xFF, 0xFF, 0xFF)
