#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import struct
import sys
sys.path.append(os.path.abspath('src'))
from gamestate import GameState

class TPMessage(object):
    METHOD_NONE = 0
    METHOD_ASKREADY = 1
    METHOD_CONFIRM = 2
    METHOD_STARTGAME = 3
    FORMAT = '!ii'
    def __init__(self):
        self.method = self.METHOD_NONE
        self.player_id = GameState.ROLE_NONE
        self.event_type = EventType.HANDSHAKE

    def getsize(self):
        return struct.calcsize(self.FORMAT)

    def pack(self): 
        return struct.pack(self.FORMAT, self.method, self.player_id)

    def unpack(self, b):
        (self.method, self.player_id) = struct.unpack(self.FORMAT, b)

    def Serialize(self):
        return self.pack()

    def Deserialize(self, b):
        self.unpack(b)


