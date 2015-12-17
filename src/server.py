#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import socket
import select
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
import upnp
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

        The last STARTGAME message contains a player_id (which determines the 
        initial role of the client).

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
                return -1
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
                return -1
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
                    return -1
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
            return -1
        logger.info('sending game start message')
        for i in range(0, len(conns)):
            sock = conns[i]
            m.method = TPMessage.METHOD_STARTGAME
            m.player_id = i
            b = m.pack()
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
        return 0

    def PlayGame(self, clients, conf):
        '''Runs the game for clients.

        Argument:
        clients -- A list of sockets connected to the clients.'''
        e = GameEngine()
        e.is_server = True
        e.is_client = False
        e.clients = clients
        conf.Apply(e)
        logger.info('sending game config')
        i = 0
        for c in clients:
            conf.player_id = i
            c.WriteEvent(conf)
            i += 1
        e.Play(e.state)

    def Run(self, addr, upnp, conf):
        '''Run the game server.

        Arguments:
        addr      -- The address of the server (ip, port).
        upnp      -- True if and only if UPnP port forwarding should be used
        conf      -- The game configuration.
        '''

        logger.info('starting server at {0}'.format(addr))
        serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversock.bind(addr)
        serversock.listen(10)
        if upnp:
            with upnp.UpnpPortMap(addr[1], 'TCP') as u:
                print ('External address: %s:%u' %
                    (u.GetExternalIp(), u.GetExternalPort()))
                self.EventLoop(conf, serversock)
        else:
            self.EventLoop(conf, serversock)
        serversock.close()

    def EventLoop(self, conf, serversock):
        while True:
            clients = self.AcceptN(serversock, conf.player_size)
            self.Handshake(clients)
            if clients.__len__() < conf.player_size:
                logger.error('handshake failed, retrying')
                continue
            evtsock_clients = [EventSocket(c) for c in clients]
            self.PlayGame(evtsock_clients, conf)
            break

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='The triplepong game server.')
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
    parser.add_argument('--fps', type=int, default=40,
            help='The frame rate in seconds')
    parser.add_argument('--delay', type=int, default=0,
            help='The frame of lag between key input and output.')
    args = parser.parse_args()
    s = TPServer()
    conf = GameConfig()
    conf.player_size = args.players
    conf.game_length = args.time
    conf.ball_vel = args.speed
    conf.rounds = args.rounds
    conf.frames_per_sec = args.fps
    conf.buffer_delay = args.delay
    # The empty string represents INADDR_ANY.
    # Using socket.INADDR_ANY will give you a type error.
    s.Run(('', args.port), upnp, conf)
