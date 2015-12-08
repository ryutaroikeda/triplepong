import os
import select
import socket
import sys
sys.path.append(os.path.abspath('src'))
from eventtype import EventType
from gamestate import GameState
from gameevent import GameEvent

class EventSocket:
    '''This class provides methods to read and write events through socket 
    connections.
    
    Attributes:
    sock        -- The socket to use.
    event_type  -- The current event being read.
    read_max    -- The total number of bytes for the current event.
    byte_buffer -- The bytes read so far.'''

    def __init__(self, sock):
        sock.setblocking(False)
        self.sock = sock
        self.event_type = 0
        self.read_max = 0
        self.byte_buffer = b''
        pass

    def ReadEvent(self):
        '''Reads an event.

        This method is (non-blocking) and will return None if no complete event
        is available.

        Return value:
        An event if available, or None.'''
        
        (socks, _, _) = select.select([self.sock], [], [], 0)
        if len(socks) == 0:
            return None
        if self.event_type == 0:
            b = self.sock.recv(EventType.GetSize())
            evt_type = EventType()
            evt_type.Deserialize(b)
            self.event_type = evt_type.event_type
            self.byte_buffer = b''
            if self.event_type == EventType.STATE_UPDATE:
                self.read_max = GameState.GetSize()
            elif self.event_type == EventType.KEYBOARD:
                self.read_max = GameEvent.GetSize()
            pass
        buf = self.sock.recv(self.read_max - len(self.byte_buffer))
        self.byte_buffer += buf
        if len(self.byte_buffer) >= self.read_max:
            if self.event_type == EventType.STATE_UPDATE:
                evt = GameState()
                evt.Deserialize(self.byte_buffer)
                self.event_type = 0
                return evt
            elif self.event_type == EventType.KEYBOARD:
                evt = GameEvent()
                evt.Deserialize(self.byte_buffer)
                self.event_type = 0
                return evt
            pass
        return None

    def WriteEvent(self, evt):
        b = evt.Serialize()
        self.sock.sendall(b)
        pass

