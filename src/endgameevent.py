import os
import struct
import sys
sys.path.append(os.path.abspath('src'))
from eventtype import EventType
class EndGameEvent:
    '''The event for signalling the end of the game.
    Attributes:
    score_N -- The final score for player N.
    '''
    FORMAT = '!iiii'
    SUBFORMAT = '!iii'
    def __init__(self):
        self.event_type = EventType.END_GAME
        self.score_0 = 0
        self.score_1 = 0
        self.score_2 = 0
        
    def __eq__(self, other):
        if other == None:
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

    def GetSize(self):
        return struct.calcsize(EndGameEvent.SUBFORMAT)

    def Serialize(self):
        return struct.pack(EndGameEvent.FORMAT, self.event_type,
                self.score_0, self.score_1, self.score_2)

    def Deserialize(self, b):
        '''
        Arguments:
        b -- The byte string.
        '''
        (self.score_0, self.score_1, self.score_2,) = \
                struct.unpack(EndGameEvent.SUBFORMAT, b)

