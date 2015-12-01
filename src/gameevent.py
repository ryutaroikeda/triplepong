import os
import sys
sys.path.append(os.path.abspath('src'))
from eventqueue import Event

class GameEvent(Event):
    EVENT_NO_OP = 0
    EVENT_FLAP_LEFT_PADDLE = 1
    EVENT_FLAP_RIGHT_PADDLE = 2
    EVENT_FLAP_BALL = 3
    def __init__(self):
        pass
    def Serialize(self):
        pass
    def Deserialize(self):
        pass
