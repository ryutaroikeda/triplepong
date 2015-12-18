import os
import select
import socket
import sys
sys.path.append(os.path.abspath('src'))
from udpdatagram import UDPDatagram
class UDPSocket:
    '''
    Attributes:
    sock      -- A socket object.
    ttl       -- The time-to-live for the connection.
    seq       -- The number of datagrams sent (16 bits).
    ack       -- The number of acknowledged datagrams (16 bits).
    ackbits   -- Acknowledgement of the previous 32 datagrams. (32 bits).
    '''
    def __init__(self):
        self.sock = None
        self.ttl = 0
        self.seq = 0
        self.ack = 0
        self.ackbits = 0

    def IsMoreRecent(self, s1, s2, maximum):
        '''
        Return value:
        True if s1 is more recent than s2, and False otherwise.
        This method takes into account integer wrapping.
        '''
        return ((s1 > s2) and (s1 - s2 <= maximum // 2) or \
                (s2 > s1) and (s2 - s1 > maximum // 2))

    def Open(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def Close(self):
        self.sock.close()

    def Bind(self, addr):
        '''Prepare to receive datagrams from ip on port.
        '''
        self.sock.bind(addr)

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
        self.sock.send(buf)
        self.seq = (self.seq + 1) % UDPDatagram.MAX_SEQ

    def UpdateAck(self, ack):
        '''Update the ack and ackbits.
        If ack is most recent, it is set as the new ack and the ackbits are 
        shifted. Otherwise, if ack is within 32 acks from the most recent, the 
        corresponding ackbit is set.
        Argument:
        ack -- The newly received sequence number.
        '''
        if ack == self.ack:
            return
        if self.IsMoreRecent(ack, self.ack, UDPDatagram.MAX_SEQ):
            if ack > self.ack:
                shift = ack - self.ack
            else:
                shift = UDPDatagram.MAX_SEQ + ack - self.ack
            self.ackbits >>= shift
            self.ackbits |= (1 << 31) >> (shift - 1)
            self.ack = ack
        else:
            if ack > self.ack:
                shift = UDPDatagram.MAX_SEQ + self.ack - ack - 1
            else:
                shift = self.ack - ack - 1
            self.ackbits |= ((1 << 31) >> shift)

    def Recv(self):
        '''Non-blocking receive.
        '''
        (ready, _, _) = select.select([self.sock], [], [], 0)
        if ready == []:
            return None
        buf = self.sock.recv(UDPDatagram.MAX_DATAGRAM)
        datagram = UDPDatagram()
        # To do: try except with logging.
        datagram.Deserialize(buf)
        self.UpdateAck(datagram.seq)
        return datagram

    def Connect(self, addr):
        '''Set the peer's address.
        '''
        self.sock.connect(addr)

    def Handshake(self, addr):
        '''Establish a connection.
        '''
        self.Connect(addr)

    def Accept(self):
        '''Try to accept a connection.
        Return value:
        A UDPSocket with the address of a peer.
        '''

        buf = self.sock.recvfrom(UDPDatagram.MAX_DATAGRAM)
        s = UDPSocket()




