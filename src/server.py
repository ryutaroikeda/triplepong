#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import socket
import select
import sys
import time
sys.path.append(os.path.abspath('src'))
import tpsocket
from tpmessage import TPMessage
import tplogger
logger = tplogger.getTPLogger('server.log', logging.DEBUG)
class TPServer(object):
    '''Implements the game server.'''
    def __init__(self):
        pass
    def AcceptN(self, svrsock, n):
        '''Return a list of n sockets connected to socket svrsock.

        This method accepts n connections to svrsock. You must call bind() and 
        listen() on svrsock before calling this.
        The sockets returned must complete the handshake protocol before a game 
        can be started, since some of the connections may have died while in 
        waiting.
        
        Arguments:
            svrsock -- the socket for accepting connections.
            n       -- the number of connections to accept.'''

        logger.info('accepting clients to join the game')
        socks = []
        while socks.__len__() < n:
            (conn, connAddr) = svrsock.accept()
            logger.info('accepted connection from {0}'.format(connAddr))
            socks.append(conn)
            pass
        logger.info('accepted connections from {0} clients'.format(n))
        return socks

    def Handshake(self, conns):
        '''Perform the handshake protocol with the sockets in conns, while 
        removing those that failed.

        The handshake ensures that clients are ready to play. conns is a list 
        of connected sockets.
        The server initiates the handshake and sends an ASKREADY message to 
        each client in conns. Each client responds with a CONFIRM message to 
        the server. After the server receives the confirmation from every 
        client, the handshake is completed successfully (from the server's
        point of view) and the server sends a STARTGAME message to each client.
        The handshake is completed successfully from the client's point of 
        view when it receives the STARTGAME message.

        The handshake may fail in one of at least two ways:
        1) the server fails to send ASKREADY to a client, probably because 
        the client closed the connection.
        2) the server times out before receiving CONFIRM from all clients.
        
        Clients that failed the handshake are removed from conns. In case 1,
        the first connection to cause the failure is closed and removed. In 
        case 2, all connections that failed to send CONFIRM prior to timeout 
        are removed.

        Clients can also be removed when the server fails to send STARTGAME. 
        We do not count this as a handshake failure. This is because some 
        clients may have received  STARTGAME already, thus completing the 
        handshake for that client. This should be dealt with elsewhere.

        Arguments:
        conns - a mutable list of sockets connected to the server.

        Return value:
        This method returns 0 upon successful completion of the handshake (for 
        the server) and -1 otherwise.'''
        logger.info('asking clients if they are ready')
        m = TPMessage()
        m.method = TPMessage.METHOD_ASKREADY
        b = m.pack()
        for sock in list(conns): # iterate over a copy of the list
            logger.debug('sending bytes {0} to {1}'.format(b, 
                sock.getpeername()))
            try:
                sock.sendall(b)
            except Exception as e:
                logger.error('removing a dead client. Handshake failed')
                sock.close()
                conns.remove(sock)
                return
            pass
        logger.info('waiting for clients to send confirmation')
        waitconns = list(conns)
        while waitconns.__len__() > 0:
            timeout = 2.0
            (socks, _, _) = select.select(waitconns,[],[],timeout)
            if socks.__len__() == 0:
                logger.error(
                        'wait for confirmations timed out. Handshake failed')
                for s in waitconns:
                    s.close()
                    pass
                return
            for sock in socks:
                logger.info('checking for confirmation')
                bufsize = m.getsize()
                b = tpsocket.recvall(sock, bufsize, 1.0)
                logger.debug('received bytes {0} from {1}'.format(b,
                    sock.getpeername()))
                try:
                    m.unpack(b)
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
        b = m.pack()
        for sock in conns:
            logger.debug('sending bytes {0}'.format(b))
            try:
                sock.sendall(b)
            except:
                logger.warning(
'client at {0} died - it\'s too late to stop game'.format(sock.getpeername()))
                sock.close()
                conns.remove(sock)
                pass
            pass
        logger.info('handshake successful')
        return conns
    # addr is the address of the server
    # clientNum is the number of clients per game
    # fork a thread and run the server. Return the pid of the child
    def Run(self, addr, clientNum) -> int:
        logger.info('starting server at {0}'.format(addr))
        # fix me: use UDP?
        serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversock.bind(addr)
        serversock.listen(10)
        while True:
            clients = self.AcceptN(serversock, clientNum)
            self.handshake(clients)
            if clients.__len__() < clientNum:
                logger.error('handshake failed, retrying')
                continue
            # to do: start the game
            break
        serversock.close()
        return 0
    pass

# to do: test dead client removal in handshake
