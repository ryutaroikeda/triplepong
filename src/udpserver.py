#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import select
import sys
import time
sys.path.append(os.path.abspath('src'))
from endgameevent import EndGameEvent
from eventtype import EventType
from gameconfig import GameConfig
from udpgameengine import UDPGameEngine
import tplogger
from tpmessage import TPMessage
from udpeventsocket import UDPEventSocket
from udpsocket import UDPSocket
#sys.path.append(os.path.abspath('profiling'))
#import lineprofiler
logger = tplogger.getTPLogger('udpserver.log', logging.DEBUG)

'''
Handling events:
Events older than size frames before bitrec.frame are ignored.
Events newer than size frames after state.frame are ignored.
'''
class UDPServer:
    '''
    Attributes:
    send_rate      -- Number of updates to send per second.
    buffer_time    -- The time in msec between invitations and game start.
    '''
    def __init__(self):
        self.game_start_time = 0.0
        self.send_rate = 15
        self.buffer_time = 5000
        self.server_behind_count = 0

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
        logger.info('Starting handshake.')
        start_time = time.time()
        end_time = start_time + timeout
        resend = conf.resend
        try:
            player_id = 0
            for c in list(conns):
                conf.player_id = player_id
                c.player_id = player_id
                sent_successfully = False
                for i in range(0, resend):
                    time_left = max(end_time - time.time(), 0)
                    status = c.WriteEvent(conf, time_left)
                    if not status == 0:
                        continue
                    sent_successfully = True
                if not sent_successfully:
                    conns.remove(c)
                    logger.error('Failed to send config to {0}'.format(
                        c.player_id))
                    return -1
                player_id += 1
        except Exception as e:
            c.Close()
            conns.remove(c)
            logger.exception(e)
            return -1
        logger.info('Waiting for confirmation.')
        waiting = list(conns)
        while time.time() < end_time and len(waiting) > 0:
            time_left = max(end_time - time.time(), 0)
            (ready, [], []) = select.select(waiting, [], [], time_left)
            if len(ready) == 0:
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
                else:
                    logger.info('Incorrect message received.')
        if len(waiting) > 0:
            logger.info('Did not get confirmation from all. Failing.')
            for c in waiting:
                c.Close()
                conns.remove(c)
            return -1
        logger.info('Sending start message.')
        msg = TPMessage()
        msg.method = TPMessage.METHOD_STARTGAME
        self.game_start_time = int(time.time() * 1000 + self.buffer_time)
        did_lose_client = False
        for c in conns:
            try:
                msg.timestamp = int(self.game_start_time + c.delta)
                logger.info('Telling client {0} to start at {1}'.format(
                    c.player_id, msg.timestamp))
                did_send = False
                for i in range(0, resend):
                    time_left = max(end_time - time.time(), 0)
                    status = c.WriteEvent(msg, time_left)
                    if status == 0:
                        did_send = True
                if not did_send:
                    raise Exception('send to {0} failed'.format(c.player_id))
            except Exception as e:
                did_lose_client = True
                logger.exception(e)
                logger.warning('A client died just before the start')
                c.Close()
                conns.remove(c)
        logger.info('Handshake succeeded.')
        if did_lose_client:
            return 1
        return 0

    def PlayFrames(self, e, s, start_time, max_frame, frame_rate):
        '''
        Play max_frame frames.
        Arguments:
        e           -- The GameEngine.
        s           -- The GameState.
        start_time  -- The time of start in seconds since the epoch
        max_frame   -- The number of frames to play.
        frame_rate  -- Frames per second.
        size        -- Number of records in e.bitrec and bit.rec.
        '''
        assert e != None
        assert s != None
        assert e.bitrec != None
        assert e.rec != None
        assert isinstance(start_time, float)
        assert frame_rate > 0.0
        start_frame = s.frame
        end_frame = start_frame + max_frame
        next_send = 0.0
        timeout = 0.0
        while True:
            now = time.time()
            if s.frame >= end_frame:
                break
            initial_frame = s.frame
            # The minimum frame of s at the end of this iteration.
            target_frame = min(e.GetCurrentFrame(start_time, frame_rate, now),
                    end_frame)
            for c in list(e.clients):
                evt = None
                try:
                    evt = c.ReadEvent()
                except Exception as ex:
                    logger.exception(ex)
                    c.Close()
                    e.clients.remove(c)
                if evt == None:
                    continue
                if evt.event_type == EventType.KEYBOARD:
                    logger.debug('Received key event {0}.'.format( evt.frame))
                    if evt.frame < initial_frame - e.buffer_size:
                        logger.debug('Event too old to be effective.')
                        continue
                    if initial_frame < evt.frame + 1 - e.buffer_size:
                        logger.info('Event too early. Ignoring.')
                        continue
                    e.UpdateBitRecordFrame(e.bitrec, 
                            max(e.bitrec.frame, evt.frame+1), e.buffer_size)
                    e.UpdateBitRecordBit(e.bitrec, evt.frame, evt.keybits,
                            c.player_id, e.buffer_size)
                    # Rewind. Set s back buffer_size frames.
                    idx = e.bitrec.frame % e.buffer_size
                    if e.bitrec.frame < e.buffer_size:
                        idx = 0
                    e.rec.states[idx].Copy(s)
                    assert s.frame <= initial_frame
            if s.frame < e.bitrec.frame - e.buffer_size:
                # BUG: This is not meant to happen.
                logger.debug('bug {0} < {1} - {2}.'.format(s.frame,
                    e.bitrec.frame, e.buffer_size))
                # Forcefully set the frame to allow PlayFromState to work. 
                s.frame = e.bitrec.frame - e.buffer_size
            if s.frame < e.bitrec.frame:
                # Play everything up to the record.
                e.PlayFromState(s, e.bitrec, e.rec, e.bitrec.frame, 
                        e.buffer_size)
            if s.frame < target_frame:
                e.UpdateBitRecordFrame(e.bitrec, target_frame, e.buffer_size)
                if s.frame < target_frame - e.buffer_size:
                    logger.debug(('Server too far behind. {0}, {1}. '
                    'Forcing catch-up.').format(s.frame, target_frame))
                    s.frame = target_frame - e.buffer_size
                    e.bitrec.Clear()
                    self.server_behind_count += 1
                e.PlayFromState(s, e.bitrec, e.rec, target_frame, 
                        e.buffer_size)
            # Send state and bitrec to clients.
            s.bits = e.bitrec.bits
            if next_send < now:
                next_send = time.time() + (1.0/self.send_rate)
                for c in list(e.clients):
                    try:
                        logger.debug('Sending frame {0}.'.format(s.frame))
                        c.WriteEvent(s)
                    except Exception as ex:
                        logger.exception(ex)
                        c.Close()
                        e.clients.remove(c)

    def PrintStats(self):
        logger.info('\nServer behind {0}'.format(self.server_behind_count))

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
                logger.info('Syncing for {0} sec at rate {1}'.format(
                    conf.sync_timeout, conf.sync_rate))
                for c in clients:
                    status = c.Sync(conf.sync_timeout, conf.sync_rate)
                    if status != 0:
                        c.Close()
                        break
                    logger.info('client ?: Latency {0} Delta {1}'.format(
                        c.latency, c.delta))
                if status == -1:
                    logger.info('Sync failed.')
                    continue
            status = self.Handshake(clients, conf, 2.0) 
            if status == -1:
                for c in clients:
                    c.Close()
                continue
            if status == 1:
                logger.info('Cancelling game.')
                evt = EndGameEvent()
                for c in clients:
                    try:
                        c.WriteEvent(evt)
                    except Exception as ex:
                        logger.exception(ex)
                    c.Close()
                continue
            logger.info('Starting game.')
            e = UDPGameEngine()
            e.is_server = True
            e.is_client = False
            e.clients = clients
            conf.Apply(e)
            e.PlayAs(e.state, self, self.game_start_time / 1000)
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
    parser.add_argument('--delay', type=int, default=1,
            help='The frame of lag between key input and output.')
    parser.add_argument('--tries', type=int, default=100,
            help='The number of attempts to run the game.')
    parser.add_argument('--timeout', type=int, default=60,
            help='The time allowed for AcceptN.')
    parser.add_argument('--resend', type=int, default=5,
            help='Number of duplicates to send in handshake')
    parser.add_argument('--nosync', default=False, action='store_true',
            help='Measure latency and clock of clients.')
    parser.add_argument('--synctimeout', type=int, default=3,
            help='Duration of sampling for Sync()')
    parser.add_argument('--syncrate', type=int, default=5,
            help='Sync messages to send per second.')
    parser.add_argument('--buffertime', type=int, default=2,
            help='The time between invitation and game start.')
    parser.add_argument('--cooldown', type=int, default=6,
            help='Minimum frames between events.')
    parser.add_argument('--ups', type=int, default=10,
            help='The number of updates to send per second.')
    args = parser.parse_args()
    s = UDPServer()
    conf = GameConfig()
    conf.player_size = args.players
    conf.game_length = args.time
    conf.ball_vel = args.speed
    conf.rounds = args.rounds
    conf.frames_per_sec = args.fps
    conf.buffer_delay = args.delay
    conf.resend = args.resend
    conf.do_sync = not args.nosync
    conf.sync_timeout = args.synctimeout
    conf.sync_rate = args.syncrate
    conf.cool_down = args.cooldown
    s.buffer_time = args.buffertime
    s.send_rate = args.ups
    sock = UDPSocket()
    sock.Open()
    # The empty string represents INADDR_ANY.
    sock.Bind(('', args.port))
    s.Run(sock, args.upnp, conf, args.tries, args.timeout)
