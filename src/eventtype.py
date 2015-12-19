import struct
class EventType:
    NONE = 0
    KEYBOARD = 1
    STATE_UPDATE = 2
    END_GAME = 3
    CONFIGURE = 4
    HANDSHAKE = 5
    FORMAT = '!i'
    def __init__(self):
        self.event_type = EventType.NONE

    def GetSize(self):
        return struct.calcsize(EventType.FORMAT)

    def Deserialize(self, b):
        (self.event_type,) = struct.unpack(EventType.FORMAT, b)

