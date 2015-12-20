#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import struct
import sys
sys.path.append(os.path.abspath('src'))
from eventtype import EventType
from gamestate import GameState

class TPMessage(object):
    METHOD_NONE = 0
    METHOD_ASKREADY = 1
    METHOD_CONFIRM = 2
    METHOD_STARTGAME = 3
    FORMAT = '!iii'
    SUBFORMAT = '!ii'
    def __init__(self):
        self.method = self.METHOD_NONE
        self.player_id = GameState.ROLE_NONE
        self.event_type = EventType.HANDSHAKE

    def __eq__(self, other):
        if other == None:
            return False
        return self.__dict__ == other.__dict__

    def GetSize(self):
        return struct.calcsize(self.SUBFORMAT)

    def Serialize(self): 
        return struct.pack(self.FORMAT, self.event_type, self.method,
                self.player_id)

    def Deserialize(self, b):
        (self.method, self.player_id) = struct.unpack(self.SUBFORMAT, b)

    def pack(self):
        return self.Serialize()

    def unpack(self, b):
        self.Deserialize(b)

    def getsize(self):
        return self.GetSize()
