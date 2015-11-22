#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import socket
import select
import sys
sys.path.append(os.path.abspath('src'))
from tpmessage import TPMessage
import tplogger
logger = tplogger.getTPLogger('server.log', logging.DEBUG)
# the game server
class TPServer(object):
    def __init(self):
        pass
    # addr is the address of the server
    # clientMax is the number of clients per game
    # fork a thread and run the server. Return the pid of the child
    def run(self, addr, clientMax) -> int:
        pid = os.fork()
        if pid > 0:
            return pid
        logger.info('starting server at {0}'.format(addr))
        serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversock.bind(addr)
        serversock.listen(10)
        readconns = [] # a list of connected clients
        while True:
            logger.info('accepting clients to join the game')
            while readconns.__len__() < clientMax:
                (conn, connAddr) = serversock.accept()
                logger.info('accepted connection from {0}'.format(connAddr))
                readconns.append(conn)
                pass
            logger.info('asking clients if they are ready')
            m = TPMessage()
            m.method = TPMessage.METHOD_ASKREADY
            for sock in list(readconns): # iterate over a copy of the list
                try:
                    sock.sendall(m.pack())
                except:
                    logger.info('removing dead connection')
                    sock.close()
                    readconns.remove(sock)
                    pass
                pass
            logger.info('checking if we still have enough clients')
            if readconns.__len__() < clientMax:
                logger.info('not enough clients - retrying')
                continue
            logger.info('waiting for clients to send confirmation')
            waitconns = list(readconns)
            while waitconns.__len__() > 0:
                timeout = 5.0
                (socks, _, _) = select.select(waitconns,[],[],timeout)
                if socks.__len__() == 0:
                    logger.info('wait for confirmation timed out - retrying')
                    for s in readconns:
                        s.close()
                        pass
                    continue
                for sock in socks:
                    logger.info('checking for confirmation')
                    bufsize = 4096
                    # to do: handle exception from unpacking
                    m.unpack(sock.recv(bufsize))
                    if m.method == TPMessage.METHOD_CONFIRM:
                        logger.info(
                    'received confirmation from {0}'.format(sock.getpeername()))
                        waitconns.remove(sock)
                        pass
                    else:
                        logger.info('invalid message')
                        pass
                    pass
                pass
            logger.info('checking if we have confirmation from all clients')
            if waitconns.__len__() != 0:
                logger.info(
                        'did not get confirmation from all clients - retrying')
                continue
            logger.info('sending game start message')
            m.method = TPMessage.METHOD_STARTGAME
            for sock in readconns:
                try:
                    sock.sendall(m.pack())
                except:
                    logger.info(
'client at {0} died - it\'s too late to stop game'.format(sock.getpeername()))
                    sock.close()
                    readconns.remove(sock)
                    pass
                pass
            logging.info('starting game')
            # to do: set up a game
            break
        serversock.close()
        return 0
    pass


