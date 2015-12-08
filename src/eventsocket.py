import os
import socket
import sys
sys.path.append(os.path.abspath('src'))
import tpsocket

class EventSocket:
    '''This class provides methods to read and write events through socket 
    connections.
    
    Attributes:
    sock       -- The socket to use.
    event_type -- The current event being read.
    read_count -- The number of bytes of the current event.
    read_max   -- The total number of bytes for the current event.'''

    def __init__(self):
        self.sock = None
        self.event_type == 0
        self.read_count = 0
        self.read_max = 0
        pass

    def ReadEvent(self):
        '''Reads an event.

        This method is non-blocking and will return None if no complete event
        is available.
        
        Return value:
        An event if available, or None.'''
        
        (socks, _, _) = select.select([self.sock], [], [], 0.0)
        if len(socks) == 0:
            return None
        if self.event_type == 0:
            timeout = 0.5
            b = tpsocket.recvall(socks[0], EventType.GetSize(), timeout)
            evt_type = EventType()
            evt_type.Deserialize(b)
            self.event_type = evt_type.event_type
            self.read_count = 0
            if self.event_type == EventType.STATE_UPDATE:
                self.read_max = GameState.GetSize()
            elif self.event_type == EventType.KEYBOARD:
                self.read_max = GameEvent.GetSize()
            pass
        if evt_type.event_type == EventType.STATE_UPDATE:
            b = tpsocket.recvall(socks[0], GameState.GetSize(), timeout)
            evt = GameState()
            evt.Deserialize(b)
            return evt
        return None

    def GetClientEvents(self, clients):
        '''Read client sockets for keyboard events.

        Arguments:
        clients -- A list of client sockets.
        Return value:
        pass
