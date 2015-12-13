
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
    def __repr__(self):
        return str(self.__dict__)
    def __eq__(self, other):
        if other == None:
            return False
        return self.__dict__ == other.__dict__
    def __ne__(self, other):
        return not self == other
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
    def GetTopRight(self, font_size):
        '''Get the position of the top right of the object.
        This method is intended to be used by the renderer to render the score
        next to objects.
        '''
        return (self.pos_x + self.half_width,
                self.pos_y - self.half_height - font_size)

    def AlignRight(self, other):
        '''Move other so that the right of self is touching the left of other.

        Argument:
        other -- The game object to align.'''

        other.pos_x = self.pos_x + self.half_width + other.half_width
        pass
    def AlignLeft(self, other):
        '''Move other so that the left of self is touching the right of other.

        Argument:
        other -- The game object to align.'''

        other.pos_x = self.pos_x - self.half_width - other.half_width
        pass
    def AlignTop(self, other):
        '''Move other so that the top of self is touching the bottom of other.

        Argument:
        other -- The game object to align.'''

        other.pos_y = self.pos_y - self.half_height - other.half_height
        pass
    def AlignBottom(self, other):
        '''Move other so that the bottom of self is touching the top of self.

        Argument:
        other -- The game object to align.'''

        other.pos_y = self.pos_y + self.half_height + other.half_height
        pass
    pass
