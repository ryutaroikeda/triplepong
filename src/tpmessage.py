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
    METHOD_SYNC = 4
    FORMAT = '!iiiiid'
    SUBFORMAT = '!iiiid'
    def __init__(self):
        self.method = self.METHOD_NONE
        self.player_id = GameState.ROLE_NONE
        self.event_type = EventType.HANDSHAKE
        self.seq = 0
        self.ack = 0
        self.timestamp = 0.0

    def __eq__(self, other):
        if other == None:
            return False
        return self.__dict__ == other.__dict__

    def GetSize(self):
        return struct.calcsize(self.SUBFORMAT)

    def Serialize(self): 
        return struct.pack(self.FORMAT, self.event_type, self.method,
                self.player_id, self.seq, self.ack,  self.timestamp)

    def Deserialize(self, b):
        (self.method, self.player_id, self.seq, self.ack, self.timestamp) = \
                struct.unpack(self.SUBFORMAT, b)

    def pack(self):
        return struct.pack(self.SUBFORMAT, self.method, self.player_id)

    def unpack(self, b):
        self.Deserialize(b)

    def getsize(self):
        return self.GetSize()
