#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import socket
import select
import sys
import time
sys.path.append(os.path.abspath('src'))
from tpmessage import TPMessage
import tplogger
logger = tplogger.getTPLogger('server.log', logging.DEBUG)
# the game server
class TPServer(object):
    def __init(self):
        pass
    # accept N connections
    # Return a list of N sockets. Some of them may have died during the wait,
    # so they must be checked via the handshake protocol.
    def acceptN(self, svrsock, n):
        logger.info('accepting clients to join the game')
        socks = []
        while socks.__len__() < n:
            (conn, connAddr) = svrsock.accept()
            logger.info('accepted connection from {0}'.format(connAddr))
            socks.append(conn)
            pass
        return socks
    # Attempt handshakes with the given sockets.
    # conns is a list of connected sockets
    # clientNum is the number of clients to get.
    # the first socket to fail the handshake is removed from conns, and this
    # function returns
    def handshake(self, conns):
        logger.info('asking clients if they are ready')
        m = TPMessage()
        m.method = TPMessage.METHOD_ASKREADY
        for sock in list(conns): # iterate over a copy of the list
            try:
                sock.sendall(m.pack())
            except:
                logger.error('removing a dead client. Handshake failed')
                sock.close()
                conns.remove(sock)
                return
            pass
        logger.info('waiting for clients to send confirmation')
        waitconns = list(conns)
        while waitconns.__len__() > 0:
            timeout = 2.0
            time.sleep(0)
            (socks, _, _) = select.select(waitconns,[],[],timeout)
            if socks.__len__() == 0:
                logger.error(
                        'wait for confirmations timed out. Handshake failed')
                for s in conns:
                    s.close()
                    pass
                return
            for sock in socks:
                logger.info('checking for confirmation')
                bufsize = 4096
                try:
                    m.unpack(sock.recv(bufsize))
                except:
                    logger.error('invalid message received. Handshake failed')
                    conns.remove(sock)
                    return
                if m.method == TPMessage.METHOD_CONFIRM:
                    logger.info(
                'received confirmation from {0}'.format(sock.getpeername()))
                    waitconns.remove(sock)
                    pass
                else:
                    logger.warning('received invalid confirmation')
                    pass
                pass
            pass
        logger.info('checking if we have confirmation from all clients')
        if waitconns.__len__() != 0:
            logger.error(
                    'did not get confirmation from all clients. '
                    + 'Handshake failed')
            return
        logger.info('sending game start message')
        m.method = TPMessage.METHOD_STARTGAME
        for sock in conns:
            try:
                sock.sendall(m.pack())
            except:
                logger.warning(
'client at {0} died - it\'s too late to stop game'.format(sock.getpeername()))
                sock.close()
                conns.remove(sock)
                pass
            pass
        logging.info('handshake successful')
        return conns
    # addr is the address of the server
    # clientNum is the number of clients per game
    # fork a thread and run the server. Return the pid of the child
    def run(self, addr, clientNum) -> int:
        logger.info('starting server at {0}'.format(addr))
        serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversock.bind(addr)
        serversock.listen(10)
        while True:
            clients = self.acceptN(serversock, clientNum)
            self.handshake(clients)
            if clients.__len__() < clientNum:
                logger.error('handshake failed, retrying')
                continue
            # to do: start the game
            break
        serversock.close()
        return 0
    pass


