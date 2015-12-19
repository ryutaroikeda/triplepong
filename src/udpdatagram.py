import struct
class UDPDatagram:
    '''The UDP datagram.

    Attributes:
    seq     -- The sequence number.
    ack     -- The last received datagram, or the remote sequence number.
    ackbits -- The ith bit acknowledges the (ack - i)th datagram.
    '''
    HEADER = '!HHI'
    MAX_DATAGRAM = 128
    MAX_PAYLOAD = MAX_DATAGRAM - struct.calcsize(HEADER)
    MAX_SEQ = (1 << 16)
    FORMAT = HEADER + '{0}s'.format(MAX_PAYLOAD)

    def __init__(self):
        self.seq = 0
        self.ack = 0
        self.ackbits = 0
        self.payload = b''

    def __eq__(self, other):
        if other == None:
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

    def Serialize(self):
        return struct.pack(self.FORMAT, self.seq, self.ack, self.ackbits, 
                self.payload)

    def Deserialize(self, buf):
        (self.seq, self.ack, self.ackbits,
                self.payload) = struct.unpack(self.FORMAT, buf)
