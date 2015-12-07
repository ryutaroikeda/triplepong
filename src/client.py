#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import socket
import sys
import time
sys.path.append(os.path.abspath('src'))
from engine import GameEngine
import tpsocket
from tpmessage import TPMessage
import tplogger
logger = tplogger.getTPLogger('client.log', logging.DEBUG)

class TPClient(object):
    def __init__(self):
        pass

    def Handshake(self, sock):
        '''Performs a handshake with the server.
        
        The handshake is described in server.py:41:Handshake()

        Arguments:
        sock -- a socket connected to a game server.
        Return value:
        This method returns 0 on successful completion of the handshake (from 
        the client's point of view) and -1 otherwise.'''

        logger.info('initiating handshake')
        logger.info('waiting for server to ask for confirmation')
        m = TPMessage()
        bufsize = m.getsize()
        b = tpsocket.recvall(sock, bufsize, 1.0)
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
        b = tpsocket.recvall(sock, bufsize, 1.0)
        logger.debug('received bytes {0}'.format(b))
        if len(b) < bufsize:
            logger.error(
                    'recv timed out on imcomplete message. Handshake failed')
            return -1
        m.unpack(b)
        if m.method != TPMessage.METHOD_STARTGAME:
            logger.error('server could not start game')
            return -1
        logger.info('handshake completed successfully')
        return 0

    def PlayGame(self, svrsock):
        '''Play the game hosted by the server. svrsock must be connected to the 
        server before calling this method.

        Argument:
        svrsock -- A socket connected to the server.'''

        #e = GameEngine(svraddr)


    def Run(self, svraddr):
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
            logger.info('connecting to {0}'.format(servaddr))
            try:
                sock.connect(servaddr)
            except:
                logger.info('connection failed, retrying')
                continue
            logger.info('initiating handshake')
            self.handshake(sock)
            logger.info('starting game')
            self.PlayGame(sock)
            pass
        sock.close()
        return 0
        pass
    pass


