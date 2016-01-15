import os
import sys
sys.path.append(os.path.abspath('src'))
from gamestate import GameState
class GameRecord:
    '''This class records the game state and key events of each frame for up 
    to size frames into the past.
    
    The states are stored in a cyclical buffer. The index of the state in
    frame f is f mod size provided f is within size frames of the most 
    recent frame in the record.
    
    Attributes:
    size      -- The maximum number of records to keep.
    available -- The number of frames recorded and available for rewind.
    states    -- The list of recorded game states.'''

    def __init__(self):
        self.size = 0
        self.available = 0
        self.states = []
        pass

    def SetSize(self, size):
        '''Set the maximum number of records to keep. This must be called 
        before calling any other method in this class.

        Argument:
        size -- The new size of the record.'''
        self.size = size
        for i in range(0, size):
            s = GameState()
            self.states.append(s)
