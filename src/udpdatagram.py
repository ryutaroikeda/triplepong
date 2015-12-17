class UDPDatagram:
    '''The UDP datagram.

    Attributes:
    seq     -- The sequence number.
    ack     -- The last received datagram, or the remote sequence number.
    ackbits -- The ith bit acknowledges the (ack - i)th datagram.
    '''
    FORMAT = '!HHI120s'
    def __init__(self):
        self.seq = 0
        self.ack = 0
        self.ackbits = 0
        self.payload = b''

    def Serialize(self):
        return struct.pack(self.FORMAT, self.seq, self.ack, self.ackbits,
                self.payload)

    def Deserialize(self, buf):
        (self.seq, self.ack, self.ackbits, self.payload) = \
                struct.unpack(self.FORMAT, buf)

    def IsMoreRecent(self, s1, s2, maximum):
        '''
        Return value:
        True if s1 is more recent than s2, and False otherwise.
        '''
        return ((s1 > s2) and (s1 - s2 <= maximum // 2) or \
                (s2 > s1) and (s2 - s1 <= maximum // 2))

