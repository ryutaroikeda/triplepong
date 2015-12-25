import logging
import os
import select
import sys
import time
sys.path.append(os.path.abspath('src'))
from eventtype import EventType
from endgameevent import EndGameEvent
from gameconfig import GameConfig
from gameevent import GameEvent
from gamestate import GameState
import tplogger
from tpmessage import TPMessage
from udpsocket import UDPSocket

logger = tplogger.getTPLogger('udpeventsocket.log', logging.DEBUG)

class UDPEventSocket:
    '''
    Attributes:
    should_ignore_old -- If True, ReadEvent ignores events with seq < sock.ack.
                         This does not affect buffered events.
    '''
    def __init__(self, sock):
        '''
        Argument:
        sock -- A UDPSocket object.
        '''
        self.sock = sock
        self.buffered_event = None
        self.should_read_buffer = False
        self.latency = 0
        self.delta = 0
        self.should_ignore_old = False

    def fileno(self):
        return self.sock.fileno()

    def ReadEvent(self):
        if self.should_read_buffer:
            self.should_read_buffer = False
            return self.buffered_event
        (ready, _, _) = select.select([self.sock.sock], [], [], 0)
        if ready == []:
            return None
        datagram = self.sock.Recv()
        evt_type = EventType()
        evt_type.Deserialize(datagram.payload[:4])
        if evt_type.event_type == EventType.STATE_UPDATE:
            evt = GameState()
        elif evt_type.event_type == EventType.KEYBOARD:
            evt = GameEvent()
        elif evt_type.event_type == EventType.END_GAME:
            evt = EndGameEvent()
        elif evt_type.event_type == EventType.CONFIGURE:
            evt = GameConfig()
        elif evt_type.event_type == EventType.HANDSHAKE:
            evt = TPMessage()
        else:
            return None
        evt.Deserialize(datagram.payload[4:evt.GetSize()+4])
        self.buffered_event = evt
        return evt

    def UnreadEvent(self):
        self.should_read_buffer = True

    def WriteEvent(self, evt):
        if evt == None:
            return
        b = evt.Serialize()
        self.sock.Send(b)

    def Close(self):
        self.sock.Close()

    def GetPeerName(self):
        return self.sock.sock.getpeername()

    def Sync(self, timeout, sync_rate):
        '''Find the average difference between this system clock and the peer.
        We measure the average latency and compare time stamps.
        This UDPSocket must be 'connected' to a peer.
        Argument:
        timeout -- The time to run this for.
        Return value: 0 on success and -1 on error.
        '''
        assert(sync_rate != 0)
        time_between_send = 1.0 / sync_rate
        last_send = 0.0
        end_time = time.time() + timeout
        n = 0
        average_rtt = 0
        average_delta = 0
        while time.time() < end_time:
            if time.time() - last_send < time_between_send:
                continue
            expected_ack = self.sock.seq
            msg = TPMessage()
            msg.method = TPMessage.METHOD_SYNC
            msg.seq = self.sock.seq
            logger.debug('Sending seq {0}.'.format(msg.seq))
            try:
                (_, ready, _) = select.select([], [self], [], 
                        max(0, end_time - time.time()))
                if ready == []:
                    continue
                start_trip = time.time()
                self.WriteEvent(msg)
                (ready, _, _) = select.select([self], [], [],
                        max(0, end_time - time.time()))
                # Read until we find the expected response.
                while True:
                    reply = None
                    (ready, _, _) = select.select([self], [], [], 0)
                    if ready == []:
                        break
                    reply = self.ReadEvent()
                    end_trip = time.time()
                    if reply.event_type != EventType.HANDSHAKE:
                        continue
                    if reply.method != TPMessage.METHOD_SYNC:
                        continue
                    # Ignore if the reply was for a different Sync message.
                    if reply.ack != expected_ack:
                        continue
                    break
                if reply == None:
                    continue
                logger.info('Received sync response.')
                average_rtt = (average_rtt * n + (end_trip - start_trip)) / \
                        (n + 1)
                average_delta = (average_delta * n + \
                        (reply.timestamp - start_trip)) / (n + 1)
                logger.info(\
                    'timestamp={0}, start={1}, delta={2}, end={3}'.format( \
                        reply.timestamp, start_trip,
                        reply.timestamp - start_trip,
                        end_trip))
                n += 1
                last_send = end_trip
            except Exception as e:
                logger.exception(e)
                return -1
        self.latency = average_rtt / 2
        self.delta = average_delta - self.latency
        return 0

    def RecvSync(self, timeout):
        '''
        Return value: 0 on success and -1 on failure.
        '''
        end_time = time.time() + timeout
        reply = TPMessage()
        reply.method = TPMessage.METHOD_SYNC
        while time.time() < end_time:
            try:
                (ready, _, _) = select.select([self], [], [],
                    max(0, end_time - time.time()))
                if ready == []:
                    continue
                msg = self.ReadEvent()
                reply.timestamp = time.time()
                if msg.event_type != EventType.HANDSHAKE:
                    break
                if msg.method != TPMessage.METHOD_SYNC:
                    break
                reply.ack = msg.seq
                (_, ready, _) = select.select([], [self], [],
                        max(0, end_time - time.time()))
                if ready == []:
                    continue
                self.WriteEvent(reply)
                logger.debug('Sent timestamp {0}.'.format(reply.timestamp))
            except Exception as e:
                logger.exception(e)
                return -1
        return 0
