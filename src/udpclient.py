#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import select
import sys
import time
sys.path.append(os.path.abspath('src'))
from engine import GameEngine
from eventtype import EventType
from gamestate import GameState
import tplogger
from gameconfig import GameConfig
from tpmessage import TPMessage
from udpeventsocket import UDPEventSocket
from udpsocket import UDPSocket
logger = tplogger.getTPLogger('udpclient.log', logging.DEBUG)
class UDPClient:
    def __init__(self):
        self.keyboard = None
        self.renderer = None
        self.conf = None
        self.unacked_1 = -1
        self.unacked_2 = -1

    def _Handshake(self, n, tries):
        for i in range(0, tries):
            clients = []
            while len(clients) < n:

                pass

        pass

    def Handshake(self, svr, resend, timeout):
        '''Perform a handshake with the server. This must be done prior to 
        starting the game. This method sets self.conf to the game configuration 
        provided by the server.
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
                svr.RecvSync(user_conf.sync_timeout)
            if not self.Handshake(svr, resend, timeout):
                sock.Close()
                logger.info('Handshake failed.')
                continue
            logger.info('Starting game.')
            self.conf.Apply(e)
            e.server = svr
            e.is_client = True
            e.is_server = False
            e.renderer = renderer
            e.keyboard = keyboard
            # To do: Apply user_conf without overriding server config.
            e.Play(e.state)
            logger.info('Game ended.')
            sock.Close()
            return True
        logger.info('Failed to start game.')
        sock.Close()
        return False

    def HandleKeyboardEvents(self):
        pass

    def HandleServerEvents(self, e, s, rec, histories, size):
        '''
        Arguments:
        e      -- The GameEngine.
        s      -- The GameState.
        rec    -- The GameRecord.
        '''
        while True:
            evt = self.server.ReadEvent()
            if evt == None:
                break
            if evt.event_type == EventType.STATE_UPDATE:
                # Update the history and rewind.
                self.ApplyStateUpdate(e, s, rec, histories, evt, size)
            elif evt.event_type == EventType.END_GAME:
                e.HandleEndGameEvent(s, evt)

    def ApplyStateUpdate(self, e, s, rec, histories, update, size):
        '''
        Updates the local state s, the record rec, and histories.
        This method is intended to be used by the client receiving a state
        update.

        If update.frame is earlier than the next buffered key event or
        later than the previous event ack, overwrite rec at update.frame and 
        rewind from there.
        If update.frame is later than the key event but earlier than 
        its ack, we don't overwrite rec at update.frame because doing so will
        temporarily 'undo' the key. Instead, we only update histories
        and rewind.

        Arguments:
        e         -- The GameEngine.
        s         -- The GameState to update.
        rec       -- The GameRecord.
        histories -- A list of size-bit histories of s.
        update    -- The update GameState.
        size      -- The history size.
        '''
        assert e != None
        assert s != None
        assert rec != None
        assert update != None
        assert rec.size == size
        should_apply_state = False
        # Update the ack status.
        if self.unacked_1 >= 0 and e.IsAcked(self.unacked_1,
                update.histories[self.player_id], update.frame):
            self.unacked_1 = self.unacked_2
            self.unacked_2 = -1
        if s.frame - update.frame > rec.available:
            # The update is too old.
            return
        if self.unacked_1 >= 0 and s.frame > update.frame:
            # We copy the update directly into rec if it occurred in the past
            # and either the unacked event hasn't triggered or the event was 
            # lost.
            if self.unacked_1 >= s.frame:
                # The unacked event hasn't triggered yet. 
                # It's safe to use the server state.
                should_apply_state = True
            elif self.unacked_1 < update.frame - size:
                # The event was lost, so revert to the server state.
                # This will probably cause a hitch, but it's necessary to 
                # keep the states consistent.
                self.unacked_1 = self.unacked_2
                self.unacked_2 = -1
                should_apply_state = True
        if should_apply_state:
            assert s.frame >= update.frame
            # Overwrite the record.
            update.Copy(rec.states[update.frame % rec.size])
            replay_from = update.frame
            rec.available = s.frame - update.frame
        else:
            replay_from = s.frame - rec.available
        e.ApplyUpdate(s, histories, rec, replay_from, update.frame,
                update.histories, size)

    def PlayFrames(self, e, s, r, rec, start_time, max_frame, frame_rate, 
            buffer_delay, key_cool_down):
        '''
        Arguments:
        e             -- The game engine.
        s             -- The game state.
        r             -- The renderer.
        rec           -- The GameRecord.
        start_time    -- The time of game start.
        max_frame     -- The number of frames to play.
        frame_rate    -- The number of frames to play per second.
        buffer_delay  -- The number of frames of delay to apply.
        key_cool_down -- The frames of delay between event triggers.

        Variables:
        key_binding   -- The key for the client. 32 is SPACE.
        '''
        assert(frame_rate > 0)
        assert(buffer_delay <= 16)
        assert(key_cool_down <= 16)
        assert(buffer_delay + key_cool_down <= 16)
        start_frame = s.frame
        end_frame = start_frame + max_frame
        player_id = e.player_id
        buffer_size = 64
        histories = [0, 0, 0]
        key_binding = 32
        key_event = e.RoleToEvent(e.roles[player_id])
        while True:
            if s.frame >= end_frame:
                break
            buffer_idx = s.frame % buffer_size
            events = 0
            # Get keyboard input and send to server.
            if self.keyboard != None:
                keys = self.keyboard.GetKeys()
                if keys[key_binding]:
                    key_buffer[player_id] |= (1 << buffer_idx)
                    events |= key_event
            # Get server updates.
            self.HandleServerEvents(e, s, rec, histories, size)
            target_frame = e.GetCurrentFrame(start_time, frame_rate, 
                    end_frame, time.time())
            while s.frame < target_frame:
                break
            break

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=\
            'The Triplepong client, UDP version.')
    parser.add_argument('--ip', type=str, default='127.0.0.1',
            help='The IP address of the server.')
    parser.add_argument('--port', type=int, default=8090, help='The port.')
    parser.add_argument('-i', '--interpolate', action='store_true',
            default=False, help='Enable interpolation')
    parser.add_argument('-b', '--buffersize', type=int, default=300,
            help='A larger buffer increases responsiveness to the server.')
    parser.add_argument('--tries', type=int, default=60,
            help='The number of attempts to connect to the server.')
    parse.add_argument('--resend', type=int, default=4,
            help='The number of duplicate messages to send during handshake.')
    parser.add_argument('--timeout', type=int, default=1,
            help='The time allowed for each connection and handshake.')
    parser.add_argument('--sync', default=False, action='store_true',
            help='Allow the server to measure latency and clock.')
    args = parser.parse_args()
    conf = GameConfig()
    conf.do_interpolate = args.interpolate
    conf.buffer_size = args.buffersize
    conf.do_sync = args.sync
    c = UDPClient()
    from renderer import Renderer
    r = Renderer()
    # For now, nothing in server's conf affects renderer.
    r.Init()
    conf.ApplyRenderer(r)
    if not c.Run((args.ip, args.port), r, r, conf, args.tries, args.resend,
            args.timeout):
        print('Timed out.')
