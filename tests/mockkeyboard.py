class MockKeyboard:
    '''A keyboard used for testing.

    You can specify the desired keyboard output for each frame by setting
    .inputs. inputs[i] == 1 corresponds to the spacebar being pressed at 
    frame i.

    Attributes:
    inputs -- The outputs for each frame.
    frame  -- The current frame.'''

    def __init__(self):
        self.inputs = []
        self.frame = 0
        pass

    def _GetNull(self):
        return (0,)*323

    def _GetSpace(self):
        return (0,)*32 + (1,) + (0,)*290

    def GetKeys(self):
        self.frame += 1
        if self.frame <= len(self.inputs) and self.inputs[self.frame - 1] == 1:
            return self._GetSpace()
        return self._GetNull()
        
