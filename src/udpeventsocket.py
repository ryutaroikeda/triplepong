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
    player_id         -- The player id of the peer, if relevant.
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
        self.player_id = 0

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
        '''Measure the latency and clock-difference to the peer.
        This UDPSocket must be 'connected' to a peer.
        self.latency will be set to half the average round-trip-time in msec.
        self.delta will be set to the estimated clock-difference in msec.

        We use Cristian's algorithm to estimate the clock difference.
        We assume clock drift is negligible over the course of the game.
        Arguments:
        timeout   -- The time allocated to this method.
        sync_rate -- The maximum number of messages to send per second.
        Return value: 0 on success and -1 on error.
        '''
        assert timeout >= 0
        assert sync_rate > 0 
        initial_seq = self.sock.seq
        time_between_send = 1.0 / sync_rate
        last_send = 0.0
        end_time = time.time() + timeout
        n = 0
        average_rtt = 0
        min_rtt = 1000000
        while time.time() < end_time:
            if time.time() - last_send < time_between_send:
                continue
            # Expect up to time_between_send * sync_rate + 1 messages
            assert self.sock.seq - initial_seq <= timeout * sync_rate
            expected_ack = self.sock.seq
            msg = TPMessage()
            msg.method = TPMessage.METHOD_SYNC
            msg.seq = self.sock.seq
            try:
                (_, ready, _) = select.select([], [self], [], 
                        max(0, end_time - time.time()))
                if ready == []:
                    continue
                logger.debug('Sending seq {0}.'.format(msg.seq))
                start_trip = time.time() 
                last_send = start_trip
                self.WriteEvent(msg)
                seq_end_time = start_trip + time_between_send
                # Wait and read until we find the expected response or timeout.
                while True:
                    reply = None
                    remaining = seq_end_time - time.time()
                    (ready, _, _) = select.select([self], [], [], remaining)
                    if ready == []:
                        break
                    reply = self.ReadEvent()
                    end_trip = time.time()
                    if reply.event_type != EventType.HANDSHAKE:
                        continue
                    if reply.method != TPMessage.METHOD_SYNC:
                        continue
                    if reply.ack != expected_ack:
                        logger.info('Reply was out of order')
                        continue
                    break
                if reply == None:
                    continue
                logger.info('Received sync response.')
                rtt = int((end_trip - start_trip) * 1000)
                delta = reply.timestamp - int(start_trip * 1000)
                if rtt < min_rtt:
                    min_rtt = rtt
                    self.delta = int(delta - (min_rtt / 2))
                average_rtt = (average_rtt * n + rtt) / (n + 1)
                logger.info(\
                    'timestamp={0}, start={1}, delta={2}, end={3}'.format( \
                        reply.timestamp, start_trip,
                        delta, end_trip))
                n += 1
            except Exception as e:
                logger.exception(e)
                return -1
        self.latency = int(average_rtt // 2)
        if n == 0:
            logger.info('Failed to get any sync data')
            return -1
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
                recv_time = time.time()
                reply.timestamp = int(recv_time * 1000)
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
