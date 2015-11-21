import struct

class TPMessage(object):
    METHOD_NONE = 0
    METHOD_ASKREADY = 1
    METHOD_CONFIRM = 2
    def __init__(self):
        self.method = 0
        pass
    def pack(self) -> bytes:
        return struct.pack('!i', self.method)
    def unpack(self, b: bytes) -> None:
        (method,) = struct.unpack('!i', b)
        self.method = method
        pass
    pass


