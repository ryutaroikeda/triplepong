#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import select
import sys
import time
sys.path.append(os.path.abspath('src'))
from eventtype import EventType
from gameconfig import GameConfig
from engine import GameEngine
import tplogger
from tpmessage import TPMessage
from udpeventsocket import UDPEventSocket
from udpsocket import UDPSocket
logger = tplogger.getTPLogger('udpserver.log', logging.DEBUG)

class UDPServer:
    '''
    Attributes:
    send_rate      -- Number of updates to send per second.
    buffer_time    -- The time between invitations and game start.
    '''
    def __init__(self):
        self.game_start_time = 0.0
        self.send_rate = 10
        self.buffer_time = 5

    def AcceptN(self, svr, socks, n, timeout):
        '''Accept until socks has n UDPEventSocket clients.
        '''
        for i in range(0, n - len(socks)):
            sock = svr.Accept(timeout)
            if sock != None:
                logger.info('Accepted connection from {0}.'.format(\
                        sock.sock.getpeername()))
                socks.append(UDPEventSocket(sock))
        return socks

    def Handshake(self, conns, conf, timeout):
        '''
        Argument:
        conns    -- A list of UDPEventSocket clients.
        conf     -- The game config to send.
        timeout  -- The timeout for the handshake.
        Return value:
        0 if the handshake succeeded. -1 if the handshake failed. 1 if at least 
        one client died after the start of game.
        '''
        start_time = time.time()
        end_time = start_time + timeout
        logger.info('Starting handshake.')
        resend = 5
        player_id = 0
        for c in list(conns):
            try:
                conf.player_id = player_id
                for i in range(0, resend):
                    c.WriteEvent(conf)
            except Exception as e:
                c.Close()
                conns.remove(c)
                logger.exception(e)
                return -1
            player_id += 1
        logger.info('Waiting for confirmation.')
        waiting = list(conns)
        while time.time() < end_time:
            if waiting == []:
                break
            (ready, [], []) = select.select(waiting, [], [], 
                    end_time - time.time())
            if ready == []:
                continue
            for c in ready:
                try:
                    reply = c.ReadEvent()
                except Exception as e:
                    c.Close()
                    conns.remove(c)
                    logger.exception(e)
                    logger.info('Bad client. Failing.')
                    return -1
                if reply == None:
                    continue
                if reply.event_type == EventType.HANDSHAKE and \
                        reply.method == TPMessage.METHOD_CONFIRM:
                    waiting.remove(c)
        if waiting != []:
            logger.info('Did not get confirmation from all. Failing.')
            for c in waiting:
                c.Close()
                conns.remove(c)
            return -1
        logger.info('Sending start message.')
        msg = TPMessage()
        msg.method = TPMessage.METHOD_STARTGAME
        self.game_start_time = time.time() + self.buffer_time
        did_lose_client = False
        for c in conns:
            try:
                msg.timestamp = self.game_start_time + c.delta
                for i in range(0, resend):
                    c.WriteEvent(msg)
            except Exception as e:
                did_lose_client = True
                logger.exception(e)
                logger.warning('A client died just before the start. '
                        + 'It is too late to stop.')
                c.Close()
                conns.remove(c)
        logger.info('Handshake succeeded.')
        if did_lose_client:
            return 1
        return 0

    def PlayFrames(self, e, s, start_time, max_frame, frame_rate):
        '''
        Play max_frame frames.
        TO DO: Discard events too far in the future.
        Arguments:
        e           -- The GameEngine.
        s           -- The GameState.
        start_time  -- The time of start.
        end_frame   -- The frame to play up to.
        frame_rate  -- Frames per second.
        size        -- Size of the history.
        '''
        assert isinstance(start_time, float)
        assert isinstance(max_frame, int)
        assert isinstance(frame_rate, int)
        assert frame_rate > 0.0
        start_frame = s.frame
        end_frame = start_frame + max_frame
        end_time = (end_frame/ frame_rate) + start_time
        next_send = 0.0
        timeout = 0.0
        while True:
            now = time.time()
            if s.frame >= end_frame:
                break
            if now >= end_time + timeout:
                break
            for c in list(e.clients):
                try:
                    evt = c.ReadEvent()
                except Exception as ex:
                    logger.exception(ex)
                    c.Close()
                    e.clients.remove(c)
                if evt == None:
                    continue
                if evt.event_type != EventType.KEYBOARD:
                    continue
                e.ApplyUpdate(s, s.histories, e.rec, rewind_from, 
                        evt.frame, evt.keybits, size)
            # Send state to clients.
            if next_send < now:
                next_send = now + (1/self.send_rate)
                for c in list(e.clients):
                    try:
                        c.WriteEvent(s)
                    except Exception as ex:
                        logger.exception(ex)
                        c.Close()
                        e.clients.remove(c)

    def Run(self, sock, upnp, conf, tries, timeout):
        '''
        Arguments:
        sock     -- The UDPSocket to accept clients on.
        upnp     --
        conf     -- The game configuration to use.
        tries    -- Number of attempts to run a game.
        timeout  -- The timeout for socket IO.
        Return value: 0 if the game ran normally, 1 if a client died during 
        handshake, and -1 on failure.
        '''
        for i in range(0, tries):
            logger.info('Accepting clients.')
            clients = []
            self.AcceptN(sock, clients, conf.player_size, timeout)
            if len(clients) < conf.player_size:
                logger.info('Not enough clients.')
                for c in clients:
                    c.Close()
                continue
            # Make clock measurements for each client.
            if conf.do_sync:
                for c in clients:
                    c.Sync(conf.sync_timeout, conf.sync_rate)
            status = self.Handshake(clients, conf, timeout) 
            if status == -1:
                for c in clients:
                    c.Close()
                continue
            logger.info('Starting game.')
            e = GameEngine()
            e.is_server = True
            e.is_client = False
            e.clients = clients
            conf.Apply(e)
            e.PlayAs(e.state, self, self.game_start_time)
            logger.info('Game ended. Exiting.')
            sock.Close()
            for c in clients:
                c.Close()
            return status
        return -1

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=\
            'The triplepong game server, UDP version.')
    parser.add_argument('--port', type=int, default=8090,
            help='The port number.')
    parser.add_argument('--upnp', action='store_true', default=False,
            help='Forward a port using UPnP')
    parser.add_argument('--players', type=int, default=3,
            help='The number of players.')
    parser.add_argument('--time', type=int, default=120,
            help='The duration of the game in seconds.')
    parser.add_argument('--speed', type=int, default=4,
            help='The speed of the ball.')
    parser.add_argument('--rounds', type=int, default=2,
            help='The number of rounds.')
    parser.add_argument('--fps', type=int, default=60,
            help='The frame rate in seconds')
    parser.add_argument('--delay', type=int, default=0,
            help='The frame of lag between key input and output.')
    parser.add_argument('--tries', type=int, default=100,
            help='The number of attempts to run the game.')
    parser.add_argument('--timeout', type=int, default=60,
            help='The time allowed for connection and handshake.')
    parser.add_argument('--sync', default=False,
            help='Measure latency and clock of clients.')
    args = parser.parse_args()
    s = UDPServer()
    conf = GameConfig()
    conf.player_size = args.players
    conf.game_length = args.time
    conf.ball_vel = args.speed
    conf.rounds = args.rounds
    conf.frames_per_sec = args.fps
    conf.buffer_delay = args.delay
    conf.do_sync = args.sync
    sock = UDPSocket()
    sock.Open()
    # The empty string represents INADDR_ANY.
    sock.Bind(('', args.port))
    s.Run(sock, args.upnp, conf, args.tries, args.timeout)
