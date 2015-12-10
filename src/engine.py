import copy
import logging
import multiprocessing
import os
import select
import sys
import time
sys.path.append(os.path.abspath('src'))
from eventtype import EventType
from eventsocket import EventSocket
from gameobject import GameObject
from gamestate import GameState
from gameevent import GameEvent
from nullrenderer import NullRenderer
from nullkeyboard import NullKeyboard
import tpsocket
import tplogger
logger = tplogger.getTPLogger('engine.log', logging.DEBUG)
'''The gameengine module.

Notes on lag compensation.
We want the user to experience as little  network latency as possible. To 
achieve this, we can perform lag compensation on the server. The server and 
client keep a record of the game state and inputs for each frame up to about 2L 
frames, where L is the latency (more precisely, the number of frames that would 
be played in that time). When the client presses a key, the game responds 
immediately. At the same time, the client sends the key press together with the 
frame number f to the server. After about L frames, the server receives these. 
To compensate for the lag L, the server rewinds to the frame when the key was 
pressed and replays all the key events received since that time. The server 
then sends back 'relevant data to represent the state' and the frame number 
f + L. The client receives 
these after another L frames. The client can then similarly rewind to frame f 
and replay any keys since that time to compute the current state.

There are at least three approaches to what the server could send. One is 
sending the state resulting from the replay. 

There is a problem when the client enters a key between frames f and f + L. 
When the client receives the state from the server at f + 2L, we only rewind 
to f + L. Since what we receive is only a response to events up to time f, 
any event between f and f + L, say f + e  will not be taken into account. To 
the client, it will look as if that event was 'cancelled' - until the client 
receives the reply for it at time f + e + 2L. A workaround would be to 
prohibit key presses for L frames after the last.

Another approach is to send a list of pairs, each pair a frame number and the 
corresponding events at that frame. This solution avoids the need for key 
press prohibition above. However, if the server takes longer than expected to 
send the reply (i.e. 2L frames), the client may not be able to rewind far 
enough into the past to correctly reproduce the state. To avoid this, the 
client must stall the game if the game record has been filled to 2L frames 
since the last reply from the server.

Alternatively, the server could send both keys and state, to get the best of 
both.

At the moment, the first solution is preferred for its simplicity.'''

class GameRecord:
    '''This class records the game state and key events of each frame for up 
    to 2L frames into the past, where 2L is the estimated number of frames 
    played during a round-trip time.

    The .states contain game states prior to PlayFrame(). This means that the 
    actual state is obtained by calling PlayFrame on the state together with 
    the entry in .events.
    
    Attributes:
    size      -- The maximum number of records to keep.
    idx       -- The index to states and events to write to next.
    available -- The number of frames recorded and available for rewind.
    states    -- The list of recorded game states.'''

    def __init__(self):
        self.size = 0
        self.idx = 0
        self.available = 0
        self.states = []
        pass

    def SetSize(self, size):
        '''Set the maximum number of records to keep. This must be called 
        before calling any other method in this class.

        Argument:
        size -- The new size of the record.'''
        self.size = size
        for i in range(0, size):
            s = GameState()
            s.Init()
            self.states.append(s)
            pass
        pass

    def AddEntry(self, s, keys):
        '''Add an entry to the game record.

        Arguments:
        s    -- The game state.
        keys -- A flag of game events.'''
        # to do: get rid of copy. dependency
        #self.states[self.idx] = copy.deepcopy(s)
        s.Copy(self.states[self.idx])
        self.states[self.idx].key_flags = keys
        self.idx = (self.idx + 1) % self.size
        if self.available < self.size:
            self.available += 1
        pass
    pass

class GameEngine(object):
    '''The game engine.

    This class contains the logic and interfaces for the game. When run as the 
    client, it takes input from the keyboard and state updates from the server. 
    When run as the server, it takes game events sent by clients.

    The client and server sockets are event sockets (eventsocket.py).

    Attributes:
    renderer           -- The renderer to use. The default is the NullRenderer 
                          which renders nothing.
    keyboard           -- The keyboard to get input from. The default is the
                          NullKeyboard which gets nothing.
    last_key_time      -- The time of the last game event sent to the server. 
    key_cool_down_time -- The minimum time between game events. See above notes 
                          on lag compensation for more details.
    player_id          -- The player ID of the client.
    clients            -- The list of client sockets.
    server             -- The socket connected to the server.'''

    K_SPACE = 32
    def __init__(self):
        self.renderer = NullRenderer()
        self.keyboard = NullKeyboard()
        self.last_key_time = 0.0
        self.key_cool_down_time = 0.200
        self.player_id = 0
        self.is_client = True
        self.is_server = False
        self.clients = []
        self.server = None
        pass
    def GetKeyboardEvents(self, s):
        '''Get the flag for the currently pressed keys.

        The keyboard events are represented by key event codes, defined in 
        gameevent.py.

        Key presses during cool-down periods are suppressed.

        Argument:
        s -- The game state.

        Return value:
        A list of keyboard event codes.'''
        keys = self.keyboard.GetKeys()
        flag = 0
        if keys[self.K_SPACE]:
            # Check if we are in cool-down.
            now = time.time()
            if now - self.last_key_time >= self.key_cool_down_time:
                self.last_key_time = now
                if s.roles[self.player_id] == GameState.ROLE_LEFT_PADDLE:
                    flag |= GameEvent.EVENT_FLAP_LEFT_PADDLE
                elif s.roles[self.player_id] == GameState.ROLE_RIGHT_PADDLE:
                    flag |= GameEvent.EVENT_FLAP_RIGHT_PADDLE
                elif s.roles[self.player_id] == GameState.ROLE_BALL:
                    flag |= GameEvent.EVENT_FLAP_BALL
                pass
            pass
        return flag

    def GetServerEvent(self, svr):
        '''Get state update from the server.

        Argument:
        svr -- The socket connected to the server.
        Return value:
        The game state sent by the server, or None if no update was 
        available.'''
        if svr == None:
            return None
        return svr.ReadEvent()

    def GetClientEvents(self, clients, current_frame):
        '''Read client sockets for keyboard events.

        Arguments:
        clients -- A list of client sockets.
        current_frame -- The frame number of the server. If an event happens in 
        the future, it should be put back.

        Return value:
        A list of game events.
        '''
        evts = []
        for c in clients:
            evt = c.ReadEvent()
            # Check if the event happens in the future.
            if evt == None:
                continue
            if evt.frame > current_frame:
                c.UnreadEvent()
                continue
            evts.append(evt)
            pass
        return evts

    def SendStateUpdate(self, clients, s):
        '''Send a partial state to the connected sockets in clients.

        Arguments:
        clients -- The clients to send to.
        s      -- The game state to send.'''
        for c in clients:
            c.WriteEvent(s)
        pass

    def SendKeyboardEvents(self, svr, s, keys):
        '''Serialize a list of game event codes and send to the server.

        Arguments:
        svr  -- The server socket to send to.
        s    -- The game state.
        keys -- A flag of game event codes, defined in gameevent.py'''
        if svr == None:
            return
        evt = GameEvent()
        evt.keys = keys
        evt.frame = s.frame
        svr.WriteEvent(evt)

    def ApplyGravity(self, s):
        '''Apply gravity to the paddles and the ball

        Arguments:
        s -- the game state'''
        PADDLE_TERM_VELOCITY = 16
        BALL_TERM_VELOCITY   = 32

        if s.paddle_left.vel_y < PADDLE_TERM_VELOCITY:
            s.paddle_left.vel_y += 1
            pass
        if s.paddle_right.vel_y < PADDLE_TERM_VELOCITY:
            s.paddle_right.vel_y += 1
            pass
        if s.ball.vel_y < BALL_TERM_VELOCITY:
            s.ball.vel_y += 1
            pass
        pass

    def ApplyEvents(self, s, keys):
        '''Apply the effect of events to the game state.

        keys should be an OR'd flag consisting of the following values defined 
        in gameevent.py:
        EVENT_FLAP_NO_OP         -- Do nothing.
        EVENT_FLAP_LEFT_PADDLE
        EVENT_FLAP_RIGHT_PADDLE
        EVENT_FLAP_BALL          -- Update the velocity.

        More events could be defined in the future.

        Arguments:
        s    -- the game state.
        evts -- a list of events to apply.'''

        PADDLE_FLAP_VEL = -12
        BALL_FLAP_VEL   = -8
        if keys & GameEvent.EVENT_FLAP_LEFT_PADDLE:
            s.paddle_left.vel_y = PADDLE_FLAP_VEL
            pass
        if keys & GameEvent.EVENT_FLAP_RIGHT_PADDLE:
            s.paddle_right.vel_y = PADDLE_FLAP_VEL
            pass
        if keys & GameEvent.EVENT_FLAP_BALL:
            s.ball.vel_y = BALL_FLAP_VEL
            pass
        pass

    def ApplyLogic(self, s):
        '''Update positions and handle collision detection.
        
        Arguments:
            s    -- the state of the game.'''

        # update positions 
        s.ball.pos_x += s.ball.vel_x
        s.ball.pos_y += s.ball.vel_y
        s.paddle_left.pos_y += s.paddle_left.vel_y
        s.paddle_right.pos_y += s.paddle_right.vel_y
        # handle collisions
        if s.paddle_left.IsCollidingWith(s.ball):
            s.paddle_left.AlignRight(s.ball)
            s.ball.vel_x = - s.ball.vel_x
            pass
        if s.paddle_right.IsCollidingWith(s.ball):
            s.paddle_right.AlignLeft(s.ball)
            s.ball.vel_x = - s.ball.vel_x
            pass
        if s.ball.IsCollidingWith(s.ball_wall_top):
            s.ball_wall_top.AlignBottom(s.ball)
            s.ball.vel_y = - s.ball.vel_y
            pass
        if s.ball.IsCollidingWith(s.ball_wall_bottom):
            s.ball_wall_bottom.AlignTop(s.ball)
            s.ball.vel_y = - s.ball.vel_y
            pass
        if s.paddle_left.IsCollidingWith(s.paddle_wall_top):
            s.paddle_wall_top.AlignBottom(s.paddle_left)
            s.paddle_left.vel_y = - s.paddle_left.vel_y
            pass
        if s.paddle_right.IsCollidingWith(s.paddle_wall_top):
            s.paddle_wall_top.AlignBottom(s.paddle_right)
            s.paddle_right.vel_y = - s.paddle_right.vel_y
            pass
        if s.paddle_left.IsCollidingWith(s.paddle_wall_bottom):
            s.paddle_wall_bottom.AlignTop(s.paddle_left)
            s.paddle_left.vel_y = - s.paddle_left.vel_y
            pass
        if s.paddle_right.IsCollidingWith(s.paddle_wall_bottom):
            s.paddle_wall_bottom.AlignTop(s.paddle_right)
            s.paddle_right.vel_y = - s.paddle_right.vel_y
            pass
        if s.ball.IsCollidingWith(s.goal_left):
            s.ball.pos_x = ( s.goal_right.pos_x + s.goal_left.pos_x ) // 2
            s.ball.pos_y = ( s.ball_wall_top.pos_y +
                    s.ball_wall_bottom.pos_y ) // 2
            s.ball.vel_x = -4
            s.ball.vel_y = 0
            s.scores[ s.players[ GameState.ROLE_RIGHT_PADDLE ] ] += 1
            pass
        if s.ball.IsCollidingWith(s.goal_right):
            s.ball.pos_x = ( s.goal_right.pos_x + s.goal_left.pos_x ) // 2
            s.ball.pos_y = ( s.ball_wall_top.pos_y +
                    s.ball_wall_bottom.pos_y ) // 2
            s.ball.vel_x = 4
            s.ball.vel_y = 0
            s.scores[ s.players[ GameState.ROLE_LEFT_PADDLE ] ] += 1
            pass
        pass

    def PlayFrame(self, s, keys):
        '''Move the game forward by one frame.

        Arguments:
        s    -- The game state.
        keys -- The flag for key events.'''
        self.ApplyGravity(s)
        self.ApplyEvents(s, keys)
        self.ApplyLogic(s)
        s.frame += 1
        s.key_flags = 0
        pass

    def RewindAndReplayWithState(self, auth_state, current_frame, rec):
        '''Rewind and replay the game from a given state.

        This method rewinds the game to auth_state.frame and replays inputs 
        starting from that frame until the current frame over auth_state. 
        auth_state will be changed.
        The inputs for the current frame are not handled here, so any events 
        must be applied to the result of this method.
        The inputs  are recorded in rec. 

        This method is intended to be used by the client receiving an 
        authoritative state auth_state from the server to correct the local 
        game state.

        Arguments:
        auth_state    -- The state to replay from. 
        current_frame -- The frame to replay to.
        rec           -- A game record.
        
        Return value:
        The game state resulting from the rewind and replay or None if 
        no rewind is possible.'''
        rewind = current_frame - auth_state.frame
        if rewind < 0:
            # The server is ahead of the client. Go to auth_state directly.
            rec.idx = 0
            auth_state.Copy(rec.states[0])
            #rec.states[0] = copy.deepcopy(auth_state)
            rec.available = 1
            return auth_state
        if rewind > rec.available:
            # The state is too old for rewind.
            # To do: handle this.
            logger.debug('ignoring old state')
            return None
        rec.states[(rec.idx - rewind) % rec.size].key_flags |= \
                auth_state.key_flags
        for i in range(0, rewind):
            self.PlayFrame(auth_state,
                    rec.states[(rec.idx - rewind + i) % rec.size].key_flags)
            pass
        rec.available = rewind
        auth_state.key_flags = 0
        return auth_state
    
    def RewindAndReplayWithKey(self, s, evt, rec):
        '''Rewind and replay the game based on events in the past.

        This method is intended to be used by the server to correct its 
        authoritative state in response to key events sent by the client.

        This method updates the event records at frame evt.frame and updates
        all later states.

        Arguments:
        s             -- The game state of the server.
        evt           -- A game event to play.
        rec           -- A game record.

        '''
        rewind = s.frame - evt.frame
        if rewind < 0:
            # The client is ahead of the server. Ignore.
            # This should never happen if we are unreading events in
            # GetClientEvents().
            logger.debug('client is ahead - ignoring')
            return None
        if rewind > rec.available:
            # The event is too old to rewind. Ignore the event.
            # To do:
            # The client needs to know the event was ignored, so return 
            # the previous frame.
            logger.debug('event too old to rewind')
            return None
        # Update the record
        rec.states[(rec.idx - rewind) % rec.size].key_flags |= evt.keys
        for i in range(0, rewind):
            idx = (rec.idx - rewind + i) % rec.size
            t = rec.states[(idx + 1) % rec.size]
            key_flags = t.key_flags
            rec.states[idx].Copy(t)
            self.PlayFrame(t, t.key_flags)
            t.key_flags = key_flags
            #s = copy.deepcopy(rec.states[idx])
            #self.PlayFrame(s, rec.states[idx].key_flags)
            #s.key_flags = rec.states[(idx + 1) % rec.size].key_flags
            #rec.states[(idx + 1) % rec.size] = s
            pass
        rec.states[rec.idx].Copy(s)
        return s
        #return copy.deepcopy(rec.states[rec.idx])

    def RunFrameAsClient(self, s, rec):
        update = None
        keys = self.GetKeyboardEvents(s)
        update = self.GetServerEvent(self.server)
        if not update == None:
            current_frame = s.frame
            s.ApplyUpdate(update)
            self.RewindAndReplayWithState(s, current_frame, rec)
            pass
        rec.AddEntry(s, keys)
        self.PlayFrame(s, keys)
        if keys != 0:
            self.SendKeyboardEvents(self.server, s, keys)
        self.renderer.RenderAll(s)
        pass

    def RunFrameAsServer(self, s, rec):
        update = None
        did_receive_client_evt = False
        key_evts = self.GetClientEvents(self.clients, s.frame)
        if len(key_evts) > 0:
            did_receive_client_evt = True
        current_frame = s.frame
        for evt in key_evts:
            self.RewindAndReplayWithKey(s, evt, rec)
            pass
        pass
        rec.AddEntry(s, rec.states[rec.idx].key_flags)
        self.PlayFrame(s, rec.states[rec.idx].key_flags)
        if did_receive_client_evt:
            self.SendStateUpdate(self.clients, s)
        self.renderer.RenderAll(s)

    def RunGame(self, s, rec, timeout):
        '''Run the game.

        This is the main game loop.

        Arguments:
        s       -- The game state to run the game from.
        rec     -- The game record for saving state and events.
        timeout -- The amount of time to run the game.'''
        start_time = time.time()
        while True:
            s.frame_start = time.time()
            if s.frame_start - start_time >= timeout:
                break
            if self.is_client:
                self.RunFrameAsClient(s, rec)
            elif self.is_server:
                self.RunFrameAsServer(s, rec)
            delta = time.time() - s.frame_start
            if 0 < delta and delta < s.sec_per_frame:
                time.sleep(s.sec_per_frame - delta)
            pass

    def PlayRotation(self, s, rec):
        '''Play one rotation of the game.

        Argument:
        s -- The game state to start the rotation from.'''

        logger.debug('starting rotation')
        self.RunGame(s, rec, s.rotation_length)

    def PlayRound(self, s, rec):
        '''Play one round of the game, with each player playing every role.

        Argument:
        s -- The game state to start the round from.'''

        logger.debug('starting round')
        for i in range(0, s.player_size):
            self.PlayRotation(s, rec)
            # rotate roles
            tmp = s.roles[1:]
            tmp.append(s.roles[0])
            s.roles = tmp
            for pid in range(0, s.player_size):
                s.players[ s.roles[pid] ] = pid
                pass
            pass
        pass

    def Play(self):
        s = GameState()
        s.Init()
        rec = GameRecord()
        # Pick an estimate for a value greater than 2L. We won't bother 
        # measuring it. 360 frames -> 6 seconds at 60 FPS should be more than 
        # enough for a decent connection, and the player wouldn't want to play 
        # on anything worse.
        rec.SetSize(360)
        for i in range(0, s.rounds):
            self.PlayRotation(s, rec)
            # self.PlayRound(s, rec)
            pass
        pass

if __name__ == '__main__':
    e = GameEngine()
    from renderer import Renderer
    r = Renderer()
    r.Init()
    e.renderer = r
    e.keyboard = r
    e.Play()
    pass
