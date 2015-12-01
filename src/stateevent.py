import os
import sys
sys.path.append(os.path.abspath('sys'))
from eventqueue import Event

class StateEvent(Event):
    '''This event describes the authoritative state of the game. The event is 
    sent by the server to the client.'''
    def __init__(self):
        pass
    def Serialize(self):
        pass
    def Deserialize(self):
        pass
    pass
