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

    def PlayGame(self, svrsock, renderer, keyboard):
        '''Play the game hosted by the server. svrsock must be connected to the 
        server before calling this method.

        Argument:
        svrsock -- A socket connected to the server.'''

        e = GameEngine()
        e.server = svrsock
        e.is_client = True
        e.is_server = False
        e.player_id = self.player_id
        e.renderer = renderer
        e.keyboard = keyboard
        s = GameState()
        e.Play(s)

    def Run(self, svraddr, renderer, keyboard):
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
            logger.info('starting game')
            self.PlayGame(EventSocket(sock), renderer, keyboard)
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
    args = parser.parse_args()
    c = TPClient()
    from renderer import Renderer
    r = Renderer()
    r.Init()
    c.Run((args.ip, args.port), r, r)
