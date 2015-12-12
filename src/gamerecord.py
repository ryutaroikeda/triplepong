import os
import sys
sys.path.append(os.path.abspath('src'))
from gamestate import GameState
class GameRecord:
    '''This class records the game state and key events of each frame for up 
    to 2L frames into the past, where 2L is the estimated number of frames 
    played during a round-trip time.

    The .states contain game states prior to PlayFrame(). This means that the 
    actual state is obtained by calling PlayFrame on the state together with 
    the entry in .events.
    
    Attributes:
    size      -- The maximum number of records to keep.
    idx       -- The index to states and events to write to next.
    available -- The number of frames recorded and available for rewind.
    states    -- The list of recorded game states.'''

    def __init__(self):
        self.size = 0
        self.idx = 0
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
            pass
        pass

    def AddEntry(self, s, keys):
        '''Add an entry to the game record.

        Arguments:
        s    -- The game state.
        keys -- A flag of game events.'''
        s.Copy(self.states[self.idx])
        self.states[self.idx].key_flags = keys
        self.idx = (self.idx + 1) % self.size
        if self.available < self.size:
            self.available += 1
        pass
    def ApplyEvent(self, frame, evt):
        '''Update the record with a key event.
        frame -- The current frame.
        evt   -- A GameEvent.

        Return value:
        0 on success. -1 if the evt cannot be applied.
        '''
        rewind = frame - evt.frame
        if rewind < 0:
            # The event is for a later frame. Ignore.
            return -1
        if rewind > self.available:
            # The event is too old. Ignore.
            return -1
        idx = (self.idx - rewind) % self.size
        self.states[idx].key_flags |= evt.keys
        return 0
    pass
