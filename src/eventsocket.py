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
    sock           -- The socket to use.
    event_type     -- The current event being read.
    read_max       -- The total number of bytes for the current event.
    byte_buffer    -- The bytes read so far.
    buffered_event -- Put back an event after reading it. Use UnreadEvent().
    should_read_buffer -- Used by UnreadEvent() and ReadEvent().
    events_read    -- The number of events read.
    '''

    def __init__(self, sock):
        sock.setblocking(False)
        self.sock = sock
        self.event_type = 0
        self.read_max = 0
        self.byte_buffer = b''
        self.buffered_event = None
        self.should_read_buffer = False
        self.events_read = 0
        pass

    def ReadEvent(self):
        '''Reads an event.

        This method is (non-blocking) and will return None if no complete event
        is available.

        If an event was read and put back with UnreadEvent(), that event will
        be returned on the next call to ReadEvent().

        Return value:
        An event if available, or None.'''

        if self.should_read_buffer:
            self.should_read_buffer = False
            return self.buffered_event
        
        (socks, _, _) = select.select([self.sock], [], [], 0)
        if len(socks) == 0:
            self.buffered_event = None
            return None
        if self.event_type == 0:
            evt_type = EventType()
            b = self.sock.recv(evt_type.GetSize())
            evt_type.Deserialize(b)
            self.event_type = evt_type.event_type
            self.byte_buffer = b''
            if self.event_type == EventType.STATE_UPDATE:
                tmp = GameState()
                self.read_max = tmp.GetSize()
            elif self.event_type == EventType.KEYBOARD:
                tmp = GameEvent()
                self.read_max = tmp.GetSize()
            pass
        buf = self.sock.recv(self.read_max - len(self.byte_buffer))
        self.byte_buffer += buf
        if len(self.byte_buffer) >= self.read_max:
            evt = None
            if self.event_type == EventType.STATE_UPDATE:
                evt = GameState()
                evt.Deserialize(self.byte_buffer)
                self.event_type = 0
            elif self.event_type == EventType.KEYBOARD:
                evt = GameEvent()
                evt.Deserialize(self.byte_buffer)
                self.event_type = 0
            self.buffered_event = evt
            self.events_read += 1
            return evt
        self.buffered_event = None
        return None

    def UnreadEvent(self):
        self.should_read_buffer = True

    def WriteEvent(self, evt):
        '''Write the event.
        If evt is None, this method does nothing.
        '''
        if evt == None:
            return
        b = evt.Serialize()
        self.sock.sendall(b)
        pass

