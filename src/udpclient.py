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

    def Handshake(self, svr, tries, timeout):
        '''Perform a handshake with the server. This must be done prior to 
        starting the game. This method sets self.conf to the game configuration 
        provided by the server.
        Argument:
        svr   -- A UDPEventSocket connected to the server.
        conf  -- The game config sent by the server.
        tries -- Number of attempts. This must be at least twice the 
                 number of duplicates sent by the server.
        timeout -- Time to wait on sockets.
        Return value:
        True if the handshake succeeded.
        '''
        logger.info('Waiting for server to initiate handshake.')
        resend = 4
        did_receive_invitation = False
        for i in range(0, tries):
            try:
                (ready, _, _) = select.select([svr], [], [], timeout)
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
        for i in range(0, tries):
            try:
                (ready, _, _) = select.select([svr], [], [], timeout)
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
                break
        if not did_receive_start:
            logger.info('Handshake timed out.')
            return False
        logger.info('Handshake succeeded.')
        return True
    
    def Run(self, svraddr, renderer, keyboard, user_conf, tries, timeout):
        '''Run the game as a client.
        Argument:
        svradr    -- The address of the server.
        renderer  -- The renderer to use.
        keyboard  -- The keyboard to use.
        user_conf -- A GameConfig provided by the user.
        tries     -- Number of tries before failing.
        timeout   -- The timeout for socket IO.
        Return value: True if a game was completed successfully.
        '''
        e = GameEngine()
        sock = UDPSocket()
        sock.Open()
        for i in range(0, tries):
            if not sock.Connect(svraddr, 1):
                logger.info('Connection failed.')
                continue
            svr = UDPEventSocket(sock)
            if not self.Handshake(svr, 20, timeout):
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

    def PlayFrames(self, e, s, r, max_frame, frame_rate, buffer_delay,
            key_cool_down):
        '''
        To do:
        Arguments:
        e             -- The game engine.
        s             -- The game state.
        r             -- The renderer.
        max_frame     -- The number of frames to play.
        frame_rate    -- The number of frames to play per second.
        buffer_delay  -- The number of frames of delay to apply.
        key_cool_down -- The frames of delay between event triggers.
        '''
        assert(frame_rate > 0)
        assert(buffer_delay <= 16)
        assert(key_cool_down <= 16)
        assert(buffer_delay + key_cool_down <= 16)
        start_time = time.time()
        start_frame = s.frame
        end_frame = start_frame + max_frame
        player_id = e.player_id
        buffer_size = 32
        key_buffer = [0, 0, 0]
        key_buffer_past = 0
        key_buffer_future = 0
        key_binding = 32
        key_event = e.RoleToEvent(e.roles[player_id])
        while True:
            if s.frame >= end_frame:
                break
            buffer_idx = s.frame % buffer_size
            events = 0
            if self.keyboard != None:
                keys = self.keyboard.GetKeys()
                if keys[key_binding]:
                    key_buffer[player_id] |= (1 << buffer_idx)
                    events |= key_event
            target_frame = e.GetTargetFrame(time.time(), start_time, 
                    start_frame, end_frame, frame_rate)
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
    args = parser.parse_args()
    conf = GameConfig()
    conf.do_interpolate = args.interpolate
    conf.buffer_size = args.buffersize
    c = UDPClient()
    from renderer import Renderer
    r = Renderer()
    # For now, nothing in server's conf affects renderer.
    r.Init()
    conf.ApplyRenderer(r)
    if not c.Run((args.ip, args.port), r, r, conf, 100, 1):
        print('Timed out.')
