import select
import socket
import struct
import time

def recvall(sock, bufsize, timeout):
    '''Tries to read bufsize bytes from socket sock until timeout.

    Return value:
    A byte string consisting of the bytes read.'''

    buf = b''
    start = time.time()
    while True: 
        delta = time.time() - start
        select_time = timeout - delta
        if select_time < 0.0:
            select_time = 0.0
        (ready, _, _) = select.select([sock], [], [], select_time)
        if ready == []:
            break
        buf += sock.recv(bufsize - len(buf))
        if len(buf)  >= bufsize:
            break
        if delta >= timeout:
            break
        pass
    return buf

        

