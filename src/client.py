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
            logger.info('waiting for server to ask for confirmation')
            m = TPMessage()
            bufsize = 4096
            try:
                m.unpack(sock.recv(bufsize))
            except Exception as e:
                logger.exception(e)
                continue
            if m.method != TPMessage.METHOD_ASKREADY:
                logger.info('received incorrect message - retrying')
                continue
            logger.info('sending confirmation')
            m.method = TPMessage.METHOD_CONFIRM
            sock.sendall(m.pack())
            logger.info('waiting for server to announce start of game')
            m.unpack(sock.recv(bufsize))
            if m.method != TPMessage.METHOD_STARTGAME:
                logger.info('server could not start game -  retrying')
                continue
            # to do: start game
            logger.info('starting game')
            break
            pass
        sock.close()
        return 0
        pass
    pass


