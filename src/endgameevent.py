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
    event_type = EventType.END_GAME
    score_0 = 0
    score_1 = 0
    score_2 = 0
    FORMAT = '!iiii'
    SUBFORMAT = '!iii'
    
    def __eq__(self, other):
        if other == None:
            return False
        return self.__dict__ == other.__dict__

    def GetSize(self):
        return struct.calcsize(self.SUBFORMAT)

    def Serialize(self):
        return struct.pack(self.FORMAT, self.event_type,
                self.score_0, self.score_1, self.score_2)

    def Deserialize(self, b):
        '''
        Arguments:
        b -- The byte string.
        '''
        (self.score_0, self.score_1, self.score_2,) = \
                struct.unpack(self.SUBFORMAT, b)

