#!/usr/bin/env python
# -*- coding: utf-8 -*-
import struct

class TPMessage(object):
    METHOD_NONE = 0
    METHOD_ASKREADY = 1
    METHOD_CONFIRM = 2
    METHOD_STARTGAME = 3
    FORMAT = '!i'
    def __init__(self):
        self.method = self.METHOD_NONE
        pass
    def getsize(self):
        return struct.calcsize(self.FORMAT)

    def pack(self) -> bytes:
        return struct.pack(self.FORMAT, self.method)
    def unpack(self, b: bytes) -> None:
        (method,) = struct.unpack(self.FORMAT, b)
        self.method = method
        pass
    pass


