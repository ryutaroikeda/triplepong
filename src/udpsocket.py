import logging
import os
import select
import socket
import sys
sys.path.append(os.path.abspath('src'))
import tplogger
from udpdatagram import UDPDatagram
logger = tplogger.getTPLogger('udpsocket.log', logging.DEBUG)
class UDPSocket:
    '''
    Constants:
    GUID_1    -- The bytes sent when initiating a handshake.
    GUID_2    -- The bytes sent when completing a handshake.
    Attributes:
    sock      -- A socket object.
    ttl       -- The time-to-live for the connection.
    seq       -- The number of datagrams sent (16 bits).
    ack       -- The number of acknowledged datagrams (16 bits).
    ackbits   -- Acknowledgement of the previous 32 datagrams. (32 bits).
    should_ignore_old -- If True, ignore datagrams earlier than the latest ack.
    '''
    MAX_TIME_TO_LIVE = 60
    GUID_1 = b'0e27b7418ee54d648b20dd82dc53905b'
    GUID_2 = b'b02dda09a088482bb8fe88df6e5268fe'
    GUID_3 = b'4200150f5d5a46a283483cc501f395e4'
    def __init__(self):
        self.sock = None
        self.ttl = 0
        self.seq = 0
        self.ack = 0
        self.ackbits = 0
        self.should_ignore_old = False

    @staticmethod
    def Pair():
        s = UDPSocket()
        t = UDPSocket()
        s.Open()
        t.Open()
        s.Bind(('127.0.0.1', 0))
        t.Bind(('127.0.0.1', 0))
        s.sock.connect(t.sock.getsockname())
        t.sock.connect(s.sock.getsockname())
        s.ttl = UDPSocket.MAX_TIME_TO_LIVE
        t.ttl = UDPSocket.MAX_TIME_TO_LIVE
        return s, t

    def fileno(self):
        return self.sock.fileno()

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
        self.sock.bind(addr)

    def Send(self, payload):
        '''
        Argument:
        payload-- The data to send.
        Return value:
        True if this method succeeded.
        '''
        datagram = UDPDatagram()
        datagram.seq = self.seq
        datagram.ack = self.ack
        datagram.ackbits = self.ackbits
        datagram.payload = payload
        buf = datagram.Serialize()
        self.sock.send(buf)
        self.seq = (self.seq + 1) % UDPDatagram.MAX_SEQ
        self.ttl -= 1
        if self.ttl <= 0:
            logger.info('The connection is dead.')
            return False
        return True

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
        datagram.Deserialize(buf)
        ignore = False
        if not self.IsMoreRecent(datagram.seq, self.ack, UDPDatagram.MAX_SEQ):
            ignore = self.should_ignore_old
        self.UpdateAck(datagram.seq)
        self.ttl = UDPSocket.MAX_TIME_TO_LIVE
        if ignore:
            return None
        return datagram

    def Connect(self, addr, timeout):
        '''Attempt to establish a connection. The peer at addr should call
        Accept().
        Return value: True if the handshake succeeded.
        '''
        (_, ready, _) = select.select([], [self.sock], [], timeout)
        if ready == []:
            logger.info('Connect timed out (1).')
            return False
        self.sock.sendto(UDPSocket.GUID_1, addr)
        (ready, _, _) = select.select([self.sock], [], [], timeout)
        if ready == []:
            logger.info('Connect timed out. (2)')
            return False
        (buf, peer_addr) = self.sock.recvfrom(len(UDPSocket.GUID_2))
        if buf != UDPSocket.GUID_2:
            logger.info('Incorrect GUID received.')
            return False
        try:
            self.sock.connect(peer_addr)
        except Exception as e:
            if e.errno != 56:
                raise e
            logger.info('Already connected.')
        (_, ready, _) = select.select([], [self.sock], [], timeout)
        if ready == []:
            logger.info('Connection timed out (3).')
            return False
        self.sock.send(UDPSocket.GUID_3)
        logger.info('Handshake succeeded.')
        self.ttl = UDPSocket.MAX_TIME_TO_LIVE
        return True

    def Accept(self, timeout):
        '''Try to accept a connection.
        Return value:
        A UDPSocket with the address of a peer, or None if the handshake 
        failed.
        '''
        (ready, _, _) = select.select([self.sock], [], [], timeout)
        if ready == []:
            logger.info('Accept timed out.')
            return None
        try:
            (buf, addr) = self.sock.recvfrom(UDPDatagram.MAX_DATAGRAM)
        except Exception as e:
            logger.exception(e)
            return None
        s = UDPSocket()
        try:
            s.Open()
            s.Bind(('', 0))
            s.sock.connect(addr)
            (_, ready, _) = select.select([], [s.sock], [], timeout)
            if ready == []:
                s.Close()
                logger.info('Accept timed out (2).')
                return None
            s.sock.send(UDPSocket.GUID_2)
            (ready, _, _) = select.select([s.sock], [], [], timeout)
            if ready == []:
                s.Close()
                logger.info('Timed out while waiting for reply.')
                return None
            buf = s.sock.recv(len(UDPSocket.GUID_3))
            if buf != UDPSocket.GUID_3:
                s.Close()
                logger.info('Incorrect GUID received.')
                return None
            logger.info('Connection accepted.')
            s.ttl = UDPSocket.MAX_TIME_TO_LIVE
            return s
        except Exception as e:
            s.Close()
            logger.exception(e)
            logger.info('Handshake failed.')
