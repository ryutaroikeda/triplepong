#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import select
import sys
import time
sys.path.append(os.path.abspath('src'))
from bitrecord import BitRecord
from engine import GameEngine
from eventtype import EventType
from gameevent import GameEvent
from gamestate import GameState
import tplogger
from gameconfig import GameConfig
from nullkeyboard import NullKeyboard
from nullrenderer import NullRenderer
from tpmessage import TPMessage
from udpeventsocket import UDPEventSocket
from udpsocket import UDPSocket
logger = tplogger.getTPLogger('udpclient.log', logging.DEBUG)
'''
Use 
assert isinstance(x, (int, long)) 
in Python 2.x
and 
assertisinstance(x, int) 
in Python 3.x.
For now, do neither.
'''
class UDPClient:
    '''
    Attributes:
    unacked_1           -- The first unacked frame.
    unacked_2           -- The second unacked frame.
    key_is_released     -- True if the key is not held down.
    loss_count          -- The number of event losses.
    state_update_count  -- The number of times the server state was used.
    old_count           -- The number of old events received.
    '''
    def __init__(self):
        self.keyboard = NullKeyboard()
        self.renderer = NullRenderer()
        self.conf = None
        self.unacked_1 = -1
        self.unacked_2 = -1
        self.key_is_released = True
        self.loss_count = 0
        self.state_update_count = 0
        self.old_count = 0

    def Handshake(self, svr, resend, timeout):
        '''Perform a handshake with the server. This must be done prior to 
        starting the game. This method sets self.conf to the game configuration 
        provided by the server.
        self.conf.start_time is sent separately and set when the start of game
        is confirmed.
        Argument:
        svr     -- A UDPEventSocket connected to the server.
        resend  -- Number of duplicate messages to send.
        timeout -- Timeout for the handshake.
        Return value:
        True if the handshake succeeded.
        '''
        start_time = time.time()
        end_time = start_time + timeout
        logger.info('Waiting for server to initiate handshake.')
        did_receive_invitation = False
        while time.time() < end_time:
            try:
                (ready, _, _) = select.select([svr], [], [], 
                        end_time - time.time())
                if ready == []:
                    continue
                msg = svr.ReadEvent()
            except Exception as e:
                logger.exception(e)
                continue
            if msg.event_type != EventType.CONFIGURE:
                continue
            self.conf = msg
            did_receive_invitation = True
            break
        if not did_receive_invitation:
            logger.info('Handshake timed out. Failing.')
            return False
        logger.info('Sending confirmation.')
        reply = TPMessage()
        reply.method = TPMessage.METHOD_CONFIRM
        for i in range(0, resend):
            try:
                svr.WriteEvent(reply)
            except Exception as e:
                logger.exception(e)
                return False           
        logger.info('Waiting for start of game.')
        did_receive_start = False
        while time.time() < end_time:
            try:
                (ready, _, _) = select.select([svr], [], [], 
                        end_time - time.time())
                if ready == []:
                    continue
                msg = svr.ReadEvent()
            except Exception as e:
                logger.exception(e)
                continue
            if msg.event_type != EventType.HANDSHAKE:
                logger.debug('Incorrect message type received.')
                continue
            if msg.method == TPMessage.METHOD_STARTGAME:
                did_receive_start = True
                self.conf.start_time = msg.timestamp
                break
        if not did_receive_start:
            logger.info('Handshake timed out.')
            return False
        logger.info('Handshake succeeded.')
        return True
    
    def Run(self, svraddr, renderer, keyboard, user_conf, tries, resend,
            timeout):
        '''Run the game as a client.
        Argument:
        svradr    -- The address of the server.
        renderer  -- The renderer to use.
        keyboard  -- The keyboard to use.
        user_conf -- A GameConfig provided by the user.
        tries     -- Number of tries before failing.
        resend    -- The number of duplicate messages to send.
        timeout   -- The timeout for socket IO.
        Return value: True if a game was completed successfully.
        '''
        e = GameEngine()
        for i in range(0, tries):
            sock = UDPSocket()
            sock.Open()
            logger.info('Connecting to server.')
            if not sock.Connect(svraddr, 1):
                sock.Close()
                logger.info('Connection failed.')
                continue
            logger.info('Connected as {0}.'.format(sock.sock.getsockname()))
            svr = UDPEventSocket(sock)
            # Allow server to make clock measurements.
            if user_conf.do_sync:
                logger.info('Syncing clock with server.')
                svr.RecvSync(user_conf.sync_timeout * 3)
            if not self.Handshake(svr, resend, timeout):
                sock.Close()
                logger.info('Handshake failed.')
                continue
            self.conf.Apply(e)
            logger.info('Starting game as player {0}.'.format(e.player_id))
            logger.debug('delay={0}, cool_down={1}'.format(e.buffer_delay,
                e.key_cool_down_time))
            e.server = svr
            e.is_client = True
            e.is_server = False
            e.renderer = renderer
            e.keyboard = keyboard
            # To do: Apply user_conf without overriding server config.
            e.PlayAs(e.state, self, self.conf.start_time)
            logger.info('Game ended.')
            logger.info('\nOld events: {0}'.format(self.old_count)+\
                    '\nLoss: {0}'.format(self.loss_count)+\
                    '\nstate update {0}'.format(self.state_update_count))
            sock.Close()
            return True
        logger.info('Failed to start game.')
        sock.Close()
        return False


    def ShouldApplyStateUpdate(self, e, frame, update_frame, update_history,
            size):
        '''
        As a side-effect, self.unacked_1 and self.unacked_2 are modified when
        they are acknowledged in update_histories or are deemed lost.

        Arguments:
        e                -- The GameEngine.
        frame            -- The current frame.
        update_frame     -- The frame of the update.
        update_history   -- History of size-bits for e.player_id.
        size             -- Size of histories.

        Return value:
        1 if we should use the server state,
        2 if an event was lost and we should use the server state and copy the
        server bitrec,
        0 if shouldn't update with the server state.
        '''
        assert e != None
        #assert isinstance(frame, (int, long))
        #assert isinstance(update_frame, (int, long))
        #assert isinstance(update_history, (int, long))
        assert isinstance(size, int)
        # Update the ack status.
        if self.unacked_1 >= 0 and e.IsAcked(self.unacked_1,
                update_history, update_frame, size):
            self.unacked_1 = self.unacked_2
            self.unacked_2 = -1
        if self.unacked_1 >= 0 and self.unacked_1 < update_frame - size:
            # The event was lost, so revert to the server state.
            # This will probably cause a hitch, but it's necessary to 
            # keep the states consistent.
            logger.debug('Event {0} was lost.'.format(self.unacked_1))
            self.unacked_1 = self.unacked_2
            self.unacked_2 = -1
            return 2
        if frame > update_frame:
            # The update is in the past.
            if self.unacked_1 == -1:
                # There are no unacked events.
                return 1 # This could be 2. Should be the same.
            if frame > update_frame and self.unacked_1 >= frame:
                # The unacked event hasn't triggered yet. 
                return 1
        return 0

    def HandleServerEvents(self, e, s, rec, size):
        '''
        Arguments:
        e      -- The GameEngine.
        s      -- The GameState.
        rec    -- The GameRecord.
        '''
        if e.server == None:
            return
        while True:
            try:
                evt = e.server.ReadEvent()
            except Exception as ex:
                logger.exception(e)
                logger.info('Disconnecting from server.')
                e.server.Close()
                e.server = None
                break
            if evt == None:
                break
            if evt.event_type == EventType.STATE_UPDATE:
                logger.info('Received state update {0}.'.format(evt.frame))
                logger.debug(('\nplayer 1: {0}\nplayer 2: {1}\n' + 
                'player 3: {2}').format(bin(evt.bits[0]),
                    bin(evt.bits[1]), bin(evt.bits[2])))
                if evt.frame < e.bitrec.frame - e.buffer_size:
                    logger.info('Update too old to be effective. ' + \
                            '{0} < {1} - {2}'.format(evt.frame,
                                e.bitrec.frame, e.buffer_size))
                    self.old_count += 1
                start_frame = s.frame
                # Update the bit records.
                # GameState evt is compatible with type BitRecord.
                e.UpdateBitRecordFrame(e.bitrec, max(e.bitrec.frame,
                    evt.frame + 1), size)
                e.UpdateBitRecord(e.bitrec, evt, size)
                should_apply_state = self.ShouldApplyStateUpdate(e, s.frame,
                        evt.frame, evt.bits[e.player_id], size)
                if should_apply_state == 2:
                    logger.debug('Handling lost event. Clearing bitrec.')
                    e.bitrec.Clear()
                    self.loss_count += 1
                if should_apply_state:
                    logger.info('Applying state update.')
                    evt.Copy(s)
                    rec.available = 0
                    self.state_update_count += 1
                else:
                    # Set up rec for rewind from oldest available frame.
                    n = start_frame - rec.available
                    e.rec.states[n % e.buffer_size].Copy(s)
            elif evt.event_type == EventType.END_GAME:
                e.HandleEndGameEvent(s, evt)

    def HandleKeyboardEvents(self, e, bitrec, frame, delay, cool_down, size):
        '''
        This method is responsible for getting keyboard input, applying
        delay, buffering, and setting bitrec.
        Arguments:
        bitrec       -- The BitRecord to update.
        frame        -- The current frame.
        delay        -- The number of frames of delay to apply.
        cool_down    -- The minimum frames between key events.
        '''
        assert e != None
        assert bitrec != None
        #assert isinstance(frame, (int, long))
        assert isinstance(delay, int)
        assert isinstance(size, int)
        assert 0 < size
        assert 0 <= delay
        assert 0 <= cool_down
        # Don't stretch the record too far.
        assert delay + cool_down <= size / 2
        ESCAPE = 27
        SPACE = 32
        keys = e.keyboard.GetKeys()
        if keys[ESCAPE]:
            raise Exception('Exited game.')
        b = 0
        if keys[SPACE] and self.key_is_released:
            b = 1
            self.key_is_released = False
        if not keys[SPACE]:
            self.key_is_released = True
        evt_frame = frame + delay
        if frame >= e.buffered_frame_1:
            # Free the second buffer.
            e.buffered_frame_1 = e.buffered_frame_2
            e.buffered_frame_2 = -1
        if frame < e.buffered_frame_1 and \
                e.buffered_frame_1 < e.buffered_frame_2:
            # Both buffers are full.
            return
        if b == 0:
            return
        if e.buffered_frame_1 < frame:
            # Fill the first buffer.
            e.buffered_frame_1 = evt_frame
            self.unacked_1 = evt_frame
        cool_down_frame = e.buffered_frame_1 + cool_down
        if frame < e.buffered_frame_1 and frame < cool_down_frame:
            # Fill the second buffer.
            e.buffered_frame_2 = cool_down_frame
            evt_frame = cool_down_frame
            self.unacked_2 = cool_down_frame
        # Update the bit in the record.
        e.UpdateBitRecordFrame(bitrec, max(evt_frame+1, bitrec.frame), size)
        bitrec.bits[e.player_id] = e.SetBit(bitrec.bits[e.player_id],
                evt_frame % size, b, size)

    def PlayFrames(self, e, s, start_time, max_frame, frame_rate):
        '''
        Arguments:
        e             -- The game engine.
        s             -- The game state.
        start_time    -- The time of game start.
        max_frame     -- The number of frames to play.
        frame_rate    -- The number of frames to play per second.
        '''
        assert e != None
        assert s != None
        assert isinstance(start_time, float)
        #assert isinstance(max_frame, (int, long))
        assert isinstance(frame_rate, int)
        assert frame_rate > 0
        assert frame_rate <= 32767
        start_frame = s.frame
        end_frame = start_frame + max_frame
        end_time = (end_frame/frame_rate)+start_time
        timeout = 0.0
        key_event = e.RoleToEvent(s.roles[e.player_id])
        send_rate = 10
        next_send = 0.0
        msg = GameEvent()
        while True:
            if s.frame >= end_frame:
                break
            now = time.time()
            if now  >= end_time + timeout:
                break
            target_frame = e.GetCurrentFrame(start_time, frame_rate, 
                    time.time())
            logger.debug('Playing from frome {0}, target {1}.'.format(s.frame,
                target_frame))
            self.HandleKeyboardEvents(e, e.bitrec, s.frame, e.buffer_delay,
                    e.key_cool_down_time, e.buffer_size)
            # Send bitrec to server.
            if e.server != None and now >= next_send:
                msg.keybits = e.bitrec.bits[e.player_id]
                msg.frame = e.bitrec.frame
                next_send = now + (1/send_rate)
                logger.debug('Sending key {0}, {1}'.format(msg.frame,
                    bin(msg.keybits)))
                try:
                    e.server.WriteEvent(msg)
                except Exception as ex:
                    logger.exception(ex)
                    logger.info('Disconnecting from server.')
                    e.server.Close()
                    e.server = None
            self.HandleServerEvents(e, s, e.rec, e.buffer_size)
            e.UpdateBitRecordFrame(e.bitrec, max(e.bitrec.frame, target_frame),
                    e.buffer_size)
            play_to = max(min(target_frame, end_frame, e.bitrec.frame), 0)
            if s.frame < e.bitrec.frame - e.buffer_size:
                logger.debug('Bit records unavailable.')
                # bail out until server update.
                # to do: reset unacked
                s.frame = e.bitrec.frame - e.buffer_size
            if s.frame < play_to:
                e.PlayFromState(s, e.bitrec, e.rec, play_to, e.buffer_size)
            e.renderer.Render(s, s, 0, 0)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=\
            'The Triplepong client, UDP version.')
    parser.add_argument('--ip', type=str, default='127.0.0.1',
            help='The IP address of the server.')
    parser.add_argument('--port', type=int, default=8090, help='The port.')
    parser.add_argument('-i', '--interpolate', action='store_true',
            default=False, help='Enable interpolation')
    parser.add_argument('-b', '--buffersize', type=int, default=64,
            help='A larger buffer increases responsiveness to the server.')
    parser.add_argument('--tries', type=int, default=60,
            help='The number of attempts to connect to the server.')
    parser.add_argument('--resend', type=int, default=4,
            help='The number of duplicate messages to send during handshake.')
    parser.add_argument('--timeout', type=int, default=10,
            help='The time allowed for each connection and handshake.')
    parser.add_argument('--nosync', default=False, action='store_true',
            help='Allow server to measure latency and clock.')
    parser.add_argument('--synctimeout', type=int, default=3,
            help='The timeout for RecvSync.')
    args = parser.parse_args()
    conf = GameConfig()
    conf.do_interpolate = args.interpolate
    conf.buffer_size = args.buffersize
    conf.do_sync = not args.nosync
    conf.sync_timeout = args.synctimeout
    c = UDPClient()
    from renderer import Renderer
    r = Renderer()
    # For now, nothing in server's conf affects renderer.
    r.Init()
    conf.ApplyRenderer(r)
    if not c.Run((args.ip, args.port), r, r, conf, args.tries, args.resend,
            args.timeout):
        print('Timed out.')
