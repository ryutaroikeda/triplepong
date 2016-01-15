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
    '''This class provides ReadEvent() and WriteEvent() for sending events
    over UDP.
    Attributes:
    sock               -- A UDPSocket.
    buffered_event   
    should_read_buffer -- Used internally by ReadEvent() and UnreadEvent().
    player_id          -- The player id of the peer if any.
    errlim             -- Number of consecutive send errors to suppress.
    errc               -- Number of consecutive send errors.
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
        self.player_id = 0
        self.errlim = 5
        self.errc = 0

    def fileno(self):
        '''Return the file descriptor of the socket.
        This method is needed for select().
        '''
        return self.sock.fileno()

    def ReadEvent(self, timeout=0):
        '''Attempt to read an event for timeout seconds.
        An event is any object that implements GetSize(), Serialize(),
        and Deserialize() and has the attribute event_type.
        '''
        if self.should_read_buffer:
            self.should_read_buffer = False
            return self.buffered_event
        (ready, _, _) = select.select([self.sock.sock], [], [], timeout)
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
        '''Undo a ReadEvent.
        The next ReadEvent will return the unread event.
        '''
        self.should_read_buffer = True

    def WriteEvent(self, evt, timeout=0.0, resend=1):
        '''Send the evt, suppressing self.errlim consecutive errors.
        This method will attempt to send at least once.
        Argument:
        evt     -- The event to send.
        timeout -- Time allocated in sec.
        resend  -- Number of times to send. If timeout > 0, sends are spaced.
        Return value:
        Return 0 on success and -1 if no events were sent.
        '''
        assert resend > 0
        if evt == None:
            return -1
        b = evt.Serialize()
        end_time = time.time() + timeout
        time_between_send = float(timeout) / resend
        next_send = 0.0
        did_send = False
        logger.debug('timeout: {0} resend: {1} tbs: {2}'.format(timeout, 
            resend, time_between_send))
        while True:
            now = time.time()
            if now < next_send:
                continue
            next_send = now + time_between_send
            try:
                (_, ready, _) = \
                    select.select([], [self.sock.sock], [], time_between_send)
                if len(ready) > 0:
                    self.sock.Send(b)
                    self.errc = 0
                    did_send = True
            except Exception as ex:
                self.errc += 1
                if self.errc > self.errlim:
                    raise ex
                logger.info('Suppressing error')
                logger.exception(ex)
            if time.time() >= end_time:
                break
        if not did_send:
            return -1
        return 0

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
                    self.delta = int(delta - (min_rtt // 2))
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
        '''The receiving end of Sync().
        Return value:
        0 on success and -1 on failure.
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
