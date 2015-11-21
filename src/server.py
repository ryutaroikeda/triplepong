import logging
import os
import socket
import select
import sys
sys.path.append(os.path.abspath('src'))
import tplogger
logger = tplogger.getTPLogger('server.log', logging.DEBUG)
# the game server
class TPServer(object):
    def __init(self):
        pass
    # addr is the address of the server
    # clientMax is the number of clients per game
    def run(self, addr, clientMax):
        logger.info('starting server at {0}'.format(addr))
        serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversock.bind(addr)
        serversock.listen(10)
        readconns = [] # the sockets to read from
        while True:
            # accept clientMax sockets
            while readconns.__len__() < clientMax:
                (conn, connAddr) = serversock.accept()
                logger.info('accepted connection from {0}'.format(connAddr))
                readconns.append(conn)
                pass
            # ask if the clients are ready to play





        pass
    pass


