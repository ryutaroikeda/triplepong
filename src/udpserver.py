import logging
import os
import select
import sys
sys.path.append(os.path.abspath('src'))
from eventtype import EventType
import tplogger
from tpmessage import TPMessage
from udpeventsocket import UDPEventSocket
from udpsocket import UDPSocket
logger = tplogger.getTPLogger('udpserver.log', logging.DEBUG)

class UDPServer:
    def AcceptN(self, svr, socks, n):
        '''Accept until socks has n sockets.
        '''
        for i in range(0, n - len(socks)):
            sock = svr.Accept(5)
            if sock != None:
                logger.info('Accepted connection.')
                socks.append(UDPEventSocket(sock))
        return socks

    def Handshake(self, conns, tries):
        '''
        Argument:
        conns    -- A list of UDPEventSocket clients.
        tries    -- The number of attempts.
        Return value:
        True if the handshake succeeded.
        '''
        logger.info('Starting handshake.')
        msg = TPMessage()
        msg.method = TPMessage.METHOD_ASKREADY
        for c in list(conns):
            try:
                c.WriteEvent(msg)
            except Exception as e:
                c.Close()
                conns.remove(c)
                logger.debug(e)
                logger.info('Bad client. Failing')
                return False
        logger.info('Waiting for confirmation.')
        waiting = list(conns)
        for i in range(0, tries):
            if waiting == []:
                break
            (ready, [], []) = select.select(waiting, [], [], .01)
            if ready == []:
                continue
            for c in ready:
                try:
                    reply = c.ReadEvent()
                except:
                    c.Close()
                    conns.remove(c)
                    logger.info('Bad client. Failing.')
                    return False
                if reply == None:
                    continue
                if reply.event_type == EventType.HANDSHAKE and \
                        reply.method == TPMessage.METHOD_CONFIRM:
                    waiting.remove(c)
        if waiting != []:
            logger.info('Did not get confirmation from all. Failing.')
            for c in waiting:
                c.Close()
                conns.remove(c)
            return False
        logger.info('Sending start message.')
        msg.method = TPMessage.METHOD_STARTGAME
        for c in conns:
            try:
                c.WriteEvent(msg)
            except:
                logger.warning('A client died just before the start. '
                        + 'It is too late to stop.')
                c.Close()
                conns.remove(c)
        logger.info('Handshake succeeded.')
        return True
