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
        if delta >= timeout:
            break
        (ready, _, _) = select.select([sock], [], [], timeout - delta)
        if ready == []:
            break
        buf += sock.recv(bufsize - len(buf))
        if len(buf)  >= bufsize:
            break
        pass
    return buf

        

