import socket
class UDPSocket:
    MAX_DATAGRAM_SIZE = 128
    MAX_SEQ           = (1 << 16)
    def __init__(self):
        '''
        Attributes:
        sock      -- A socket object.
        port      -- The port of this end.
        peer_ip   -- The IP address of the other end.
        peer_port -- The port of the other end.
        ttl       -- The time-to-live for the connection.
        seq       -- The number of datagrams sent (16 bits).
        ack       -- The number of acknowledged datagrams (16 bits).
        ackbits   -- (32 bits).
        '''
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.port = 0
        self.peer_ip = ''
        self.peer_port = 0
        self.ttl = 0
        self.seq = 0
        self.ack = 0
        self.ackbits = 0

    def IsMoreRecent(self, s1, s2, maximum):
        '''
        Return value:
        True if s1 is more recent than s2, and False otherwise.
        '''
        return ((s1 > s2) and (s1 - s2 <= maximum // 2) or \
                (s2 > s1) and (s2 - s1 > maximum // 2))


    def Bind(self, ip, port):
        '''Prepare to receive datagrams from ip on port.
        '''
        self.port = port
        self.peer_ip = ip
        self.sock.bind((self.peer_ip, self.port))

    def Send(self, payload):
        '''
        Argument:
        payload-- The data to send.
        '''
        datagram = UDPDatagram()
        datagram.seq = self.seq
        datagram.ack = self.ack
        datagram.ackbits = self.ackbits
        datagram.payload = payload
        buf = datagram.Serialize()
        self.sock.sendto(buf, (self.peer_ip, peer_port))
        self.seq += 1

    def UpdateAck(self, ack):
        '''
        Argument:
        ack -- The newly received ack.
        '''
        if ack == self.ack:
            return
        if self.IsMoreRecent(ack, self.ack, self.MAX_SEQ):
            if ack > self.ack:
                shift = ack - self.ack
            else:
                shift = self.MAX_SEQ + ack - self.ack
            self.ackbits >>= shift
            self.ackbits |= (1 << 31) >> (shift - 1)
            self.ack = ack
        else:
            if ack > self.ack:
                shift = self.MAX_SEQ + self.ack - ack - 1
            else:
                shift = self.ack - ack - 1
            self.ackbits |= ((1 << 31) >> shift)


    def Recv(self):
        buf = self.sock.recvfrom(self.MAX_DATAGRAM_SIZE)
        datagram = UDPDatagram()
        datagram.Deserialize(buf)

    def Connect(self, ip, port):
        '''Attempt to connect to ip at port.
        '''
        
        pass

    def Accept(self):
        '''Try to accept a connection.
        Return value:
        A UDPSocket connected to some end point.
        '''
        (buf, addr) = self.sock.recvfrom(self.MAX_DATAGRAM_SIZE)



