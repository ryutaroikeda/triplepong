import logging
import os
import select
import sys
sys.path.append(os.path.abspath('src'))
from eventtype import EventType
import tplogger
from tpmessage import TPMessage
from udpsocket import UDPSocket
logger = tplogger.getTPLogger('udpclient.log', logging.DEBUG)
class UDPClient:
    def Handshake(self, svr, tries):
        '''
        Argument:
        svr   -- A UDPSocket connected to the server.
        tries -- Number of attempts.
        Return value:
        True if the handshake succeeded.
        '''
        logger.info('Waiting for server to initiate handshake.')
        did_receive_invitation = False
        for i in range(0, tries):
            (ready, _, _) = select.select([svr], [], [], 1)
            if ready == []:
                continue
            msg = svr.ReadEvent()
            if msg.event_type != EventType.HANDSHAKE:
                continue
            if msg.method == TPMessage.METHOD_ASKREADY:
                did_receive_invitation = True
                break
        if not did_receive_invitation:
            logger.info('Handshake timed out. Failing.')
            return False
        logger.info('Sending confirmation.')
        reply = TPMessage()
        reply.method = TPMessage.METHOD_CONFIRM
        svr.WriteEvent(reply)
        logger.info('Waiting for start of game.')
        did_receive_start = False
        for i in range(0, tries):
            (ready, _, _) = select.select([svr], [], [], 1)
            if ready == []:
                continue
            msg = svr.ReadEvent()
            if msg.event_type != EventType.HANDSHAKE:
                continue
            if msg.method == TPMessage.METHOD_STARTGAME:
                did_receive_start = True
                break
        if not did_receive_start:
            logger.info('Handshake failed.')
            return False
        logger.info('Handshake succeeded.')
        return True
