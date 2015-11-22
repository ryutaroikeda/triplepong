#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import socket
import sys
import time
sys.path.append(os.path.abspath('src'))
from tpmessage import TPMessage
import tplogger
logger = tplogger.getTPLogger('client.log', logging.DEBUG)
class TPClient(object):
    def __init__(self):
        pass
    # handshake to start a game session
    # sock is a socket connected to the game server
    def handshake(self, sock):
        logger.info('initiating handshake')
        logger.info('waiting for server to ask for confirmation')
        bufsize = 4096
        b = sock.recv(bufsize)
        logger.info('message received. Unpacking...')
        m = TPMessage()
        m.unpack(b)
        if m.method != TPMessage.METHOD_ASKREADY:
            logger.error('received incorrect message')
            return
        logger.info('sending confirmation')
        m.method = TPMessage.METHOD_CONFIRM
        sock.sendall(m.pack())
        logger.info('waiting for server to announce start of game')
        m.unpack(sock.recv(bufsize))
        if m.method != TPMessage.METHOD_STARTGAME:
            logger.error('server could not start game')
            return
        logger.info('handshake completed successfully')
        pass

    def run(self, servaddr):
        pid = os.fork()
        if pid > 0:
            return pid
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
            pass
        sock.close()
        return 0
        pass
    pass


