#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import socket
import sys
import time
sys.path.append(os.path.abspath('src'))
from eventsocket import EventSocket
from engine import GameEngine
from gameconfig import GameConfig
from gamestate import GameState
import tpsocket
from tpmessage import TPMessage
import tplogger
logger = tplogger.getTPLogger('client.log', logging.DEBUG)

class TPClient(object):
    def __init__(self):
        self.player_id = 0
        pass

    def Handshake(self, sock, timeout):
        '''Performs a handshake with the server.
        
        The handshake is described in server.py:41:Handshake()

        After a successful handshake, .player_id is set to the value specified 
        by the server.

        Arguments:
        sock    -- A socket connected to a game server.
        timeout -- The maximum time to wait for each reply from the server, in 
        seconds.

        Return value:
        This method returns 0 on successful completion of the handshake (from 
        the client's point of view) and -1 otherwise.'''

        logger.info('initiating handshake')
        logger.info('waiting for server to ask for confirmation')
        m = TPMessage()
        bufsize = m.getsize()
        b = tpsocket.recvall(sock, bufsize, timeout)
        logger.info('message received')
        if len(b) < bufsize:
            logger.error(
                    'recv timed out on incomplete message. Handshake failed')
            return -1
        m.unpack(b)
        if m.method != TPMessage.METHOD_ASKREADY:
            logger.error('received incorrect message')
            return -1
        logger.info('sending confirmation')
        m.method = TPMessage.METHOD_CONFIRM
        sock.sendall(m.pack())
        logger.info('waiting for server to announce start of game')
        b = tpsocket.recvall(sock, bufsize, timeout)
        logger.debug('received bytes {0}'.format(b))
        if len(b) < bufsize:
            logger.error(
                    'recv timed out on imcomplete message. Handshake failed')
            return -1
        m.unpack(b)
        if m.method != TPMessage.METHOD_STARTGAME:
            logger.error('server could not start game')
            return -1
        self.player_id = m.player_id
        logger.info('handshake completed successfully')
        return 0

    def PlayGame(self, svrsock, renderer, keyboard, conf):
        '''Play the game hosted by the server. svrsock must be connected to the 
        server before calling this method.

        Receive the game configuration before running the game.

        Argument:
        svrsock -- A socket connected to the server.'''
        e = GameEngine()
        svrconf = None
        logger.info('waiting for server game config')
        while svrconf == None:
            svrconf = svrsock.ReadEvent()
        logger.info('received server game config')
        svrconf.Apply(e)
        e.server = svrsock
        e.is_client = True
        e.is_server = False
        e.renderer = renderer
        e.keyboard = keyboard
        e.buffer_size = conf.buffer_size
        logger.info('starting game as player {0}'.format(e.player_id))
        e.Play(e.state)

    def Run(self, svraddr, renderer, keyboard, conf):
        '''Run the game as a client.

        This method attempts to connect to the game server at svraddr and start 
        the game. This involves making a TCP connection and performing a 
        server-clients handshake described in server.py. Upon success, the game 
        engine is run.

        Argument:
        svraddr - the address of the server as a tuple (ip, port).'''

        sock = None
        while True:
            if sock != None:
                sock.close()
                pass
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            logger.info('connecting to {0}'.format(svraddr))
            try:
                sock.connect(svraddr)
            except:
                logger.info('connection failed, retrying')
                continue
            logger.info('initiating handshake')
            if self.Handshake(sock, 60) == -1:
                continue
            # Disable Nagel's algorithm
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
            self.PlayGame(EventSocket(sock), renderer, keyboard, conf)
            break
        sock.close()
        return 0
        pass
    pass

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='The Triplepong client.')
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
    c = TPClient()
    from renderer import Renderer
    r = Renderer()
    # For now, nothing in server's conf affects renderer.
    r.Init()
    conf.ApplyRenderer(r)
    c.Run((args.ip, args.port), r, r, conf)
