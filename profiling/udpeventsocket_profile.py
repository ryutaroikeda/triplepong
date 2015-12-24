import os
import sys
sys.path.append(os.path.abspath('src'))
from udpeventsocket import UDPEventSocket
from udpsocket import UDPSocket

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=\
            'Measure the network latency over UDP.')
    parser.add_argument('--ip', type=str, default='',
            help='The IP address of the other end (or your IP in ' +
            'listen mode).')
    parser.add_argument('--port', type=int, default=8091,
            help='The port of the other end (or your port in ' +
            'listen mode).')
    parser.add_argument('--timeout', type=int, default=5,
            help='The time to run this.')
    parser.add_argument('-l', '--listen', action='store_true',
            default=False, help='Listen for Sync().')
    args = parser.parse_args()
    s = UDPSocket()
    s.Open()
    if args.listen:
        s.Bind((args.ip, args.port))
        ss = s.Accept(args.timeout)
        if ss == None:
            exit('Accept timed out.')
        e = UDPEventSocket(ss)
        if e.RecvSync(args.timeout) == -1:
            print('RecvSync failed')
        ss.Close()
        s.Close()
    else:
        if not s.Connect((args.ip, args.port), args.timeout):
            s.Close()
            exit('Connection failed.')
        e = UDPEventSocket(s)
        if e.Sync(args.timeout) == -1:
            printf('Sync failed')
        s.Close()
        print('Latency={0}\nDelta={1}'.format(e.latency, e.delta))

