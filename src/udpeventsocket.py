import os
import select
import sys
sys.path.append(os.path.abspath('src'))
from eventtype import EventType
from endgameevent import EndGameEvent
from gameconfig import GameConfig
from gameevent import GameEvent
from gamestate import GameState
from tpmessage import TPMessage
from udpsocket import UDPSocket

class UDPEventSocket:
    def __init__(self, sock):
        '''
        Argument:
        sock -- A UDPSocket object.
        '''
        self.sock = sock
        self.buffered_event = None
        self.should_read_buffer = False

    def fileno(self):
        return self.sock.fileno()

    def ReadEvent(self):
        if self.should_read_buffer:
            self.should_read_buffer = False
            return self.buffered_event
        (ready, _, _) = select.select([self.sock.sock], [], [], 0)
        if ready == []:
            return None
        datagram = self.sock.Recv()
        evt_type = EventType()
        evt_type.Deserialize(datagram.payload[:4])
        if evt_type.event_type == EventType.STATE_UPDATE:
            evt = GameState()
        elif evt_type.event_type == EventType.KEYBOARD:
            evt = GameEvent()
        elif evt_type.event_type == EventType.END_GAME:
            evt = EndGameEvent()
        elif evt_type.event_type == EventType.CONFIGURE:
            evt = GameConfig()
        elif evt_type.event_type == EventType.HANDSHAKE:
            evt = TPMessage()
        else:
            return None
        evt.Deserialize(datagram.payload[4:evt.GetSize()+4])
        self.buffered_event = evt
        return evt

    def UnreadEvent(self):
        self.should_read_buffer = True

    def WriteEvent(self, evt):
        if evt == None:
            return
        b = evt.Serialize()
        self.sock.Send(b)

    def Close(self):
        self.sock.Close()

    def GetPeerName(self):
        return self.sock.sock.getpeername()
