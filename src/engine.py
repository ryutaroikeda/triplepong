import copy
import logging
import multiprocessing
import os
import sys
import time
import pygame
sys.path.append(os.path.abspath('src'))
from gameobject import GameObject
from gamestate import GameState
from gameevent import GameEvent
from renderer import Renderer
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
    to 2L frames into the past, where 2L is the estimated number of frames to 
    be played during a round-trip time.
    
    Attributes:
    size   -- The maximum number of records to keep.
    idx    -- The index to states and events to write to next.
    states -- The recorded game states.
    events -- The recorded key events.'''
    def __init__(self):
        self.size = 0
        self.idx = 0
        self.states = []
        self.events = []
        pass

    def SetSize(self, size):
        '''Set the maximum number of records to keep. This must be called 
        before calling any other method in this class.

        Argument:
        size -- The new size of the record.'''
        self.size = size
        for i in range(0, size):
            self.states.append(0)
            self.events.append(0)
            pass
        pass

    def AddEntry(self, s, evts):
        '''Add an entry to the game record.

        Arguments:
        s    -- The game state.
        evts -- A list of game events.'''
        self.states[self.idx] = s
        self.events[self.idx] = evts
        self.idx = (self.idx + 1) % self.size
        pass
        
    pass

class GameEngine(object):
    '''The game engine.

    This class contains the logic and interfaces for the game. When run as the 
    client, it takes input from the keyboard and state updates from the server. 
    When run as the server, it takes game events sent by clients.

    Attributes:
    last_key_time      -- The time of the last game event sent to the server. 
    key_cool_down_time -- The minimum time between game events. See above notes 
                          on lag compensation for more details.
    player_id          -- The player ID of the client.
    clients            -- The list of client sockets.
    server             -- The socket connected to the server.'''

    def __init__(self):
        self.last_key_time = 0.0
        self.key_cool_down_time = 0.200
        self.player_id = 0
        self.is_client = True
        self.is_server = False
        self.clients = []
        self.server = None
        pass
    def GetKeyboardEvents(self, s):
        '''Create a list of keyboard events.

        The keyboard events are represented by key event codes, defined in 
        gameevent.py.

        Key presses during cool-down periods are suppressed.

        Argument:
        s -- The game state.

        Return value:
        A list of keyboard event codes.'''
        evts = []
        # Events should be pumped before calling get_pressed(). These functions 
        # are wrappers for SDL functions intended to be used in this way.
        # See https://www.pygame.org/docs/ref/
        # key.html#comment_pygame_key_get_pressed
        pygame.event.pump()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            # Check if we are in cool-down.
            now = time.time()
            if now - self.last_key_time >= self.key_cool_down_time:
                self.last_key_time = now
                if s.roles[self.player_id] == GameState.ROLE_LEFT_PADDLE:
                    evts.append(GameEvent.EVENT_FLAP_LEFT_PADDLE)
                elif s.roles[self.player_id] == GameState.ROLE_RIGHT_PADDLE:
                    evts.append(GameEvent.EVENT_FLAP_RIGHT_PADDLE)
                elif s.roles[self.player_id] == GameState.ROLE_BALL:
                    evts.append(GameEvent.EVENT_FLAP_BALL)
                pass
            pass
        return evts

    def GetServerEvent(self):
        '''Get state update from the server.

        Return value:
        The game state sent by the server, or None if no update was 
        available.'''
        if self.server == None:
            return None
        (svrs, _, _) = select.select([self.server], [], [], 0.0)
        if len(svrs) == 0:
            return None
        b = tpsocket.recvall(svrs[0], EventType.GetSize(), 0.0)
        evt_type = EventType()
        evt_type.unpack(b)
        if evt_type.evt_type == EventType.STATE_UPDATE:
            b = tpsocket.recvall(svrs[0], GameState.GetSize(), 0.0)
            evt = GameState()
            evt.unpack(b)
            return evt
        return None

    def GetClientEvents(self):
        evts = []
        # Read client sockets for key events.
        timeout = 0.0
        (clients, _, _) = select.select(self.clients, [], [], timeout)
        for c in clients:
            b = tpsocket.recvall(c, EventType.GetSize(), timeout)
            evt_type = EventType()
            evt_type.Deserialize(b)
            if evt_type.evt_type == EventType.KEYBOARD:
                b = tpsocket.recvall(c, GameEvent.GetSize(), timeout)
                evt = GameEvent()
                evt.Deserialize(b)
                evts.extend(evt.keys)
                pass
            pass
        return evts

    def GetEvents(self, s):
        '''Return a list of events to apply.

        Return value:
        The list of events that should be applied to the current frame. Each 
        event is a value defined in GameEvent (see ApplyEvents() and 
        gameevent.py).

        To do: Use EventQueue and move the keyboard event getter elsewhere.
        To do: Allow user to configure key bindings.

        Arguments:
        s -- The game state.'''
        evts = []
        if self.is_client:
            evts.extend(self.GetKeyboardEvents(s))

        return evts

    def SendEvents(self, evts):
        '''Serialize game events and send to the server.

        Arguments:
        s    -- The game state.
        evts -- the list of events to send'''

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

    def ApplyEvents(self, s, evts):
        '''Apply the effect of events to the game state.

        evts should be a list consisting of the following values defined 
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
        for e in evts:
            if e == GameEvent.EVENT_FLAP_LEFT_PADDLE:
                s.paddle_left.vel_y = PADDLE_FLAP_VEL
                pass
            if e == GameEvent.EVENT_FLAP_RIGHT_PADDLE:
                s.paddle_right.vel_y = PADDLE_FLAP_VEL
                pass
            if e == GameEvent.EVENT_FLAP_BALL:
                s.ball.vel_y = BALL_FLAP_VEL
                pass
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
            s.ball.pos_x = ( s.goal_right.pos_x + s.goal_left.pos_x ) / 2
            s.ball.pos_y = ( s.ball_wall_top.pos_y +
                    s.ball_wall_bottom.pos_y ) / 2
            s.ball.vel_x = -4
            s.ball.vel_y = 0
            s.scores[ s.players[ GameState.ROLE_RIGHT_PADDLE ] ] += 1
            pass
        if s.ball.IsCollidingWith(s.goal_right):
            s.ball.pos_x = ( s.goal_right.pos_x + s.goal_left.pos_x ) / 2
            s.ball.pos_y = ( s.ball_wall_top.pos_y +
                    s.ball_wall_bottom.pos_y ) / 2
            s.ball.vel_x = 4
            s.ball.vel_y = 0
            s.scores[ s.players[ GameState.ROLE_LEFT_PADDLE ] ] += 1
            pass
        pass

    def PlayFrame(self, s, evts):
        '''Move the game forward by one frame.

        Arguments:
        s    -- The game state.
        evts -- The game events to apply.'''
        self.ApplyGravity(s)
        self.ApplyEvents(s, evts)
        self.ApplyLogic(s)
        pass

    def RewindAndReplayWithState(self, auth_state, current_frame, rec):
        '''Rewind and replay the game from a given state.

        This method rewinds the game to auth_state.frame and replays inputs 
        from that frame until the current frame over auth_state. 
        The inputs for the current frame are not handled here, so any events 
        must be applied to the result of this method.
        The inputs  are recorded in rec. Records older than auth_state.frame 
        are  discarded  from rec.

        This method is intended to be used by the client receiving an 
        authoritative state auth_state from the server to correct the local 
        game state.

        Arguments:
        auth_state    -- The state to replay from. 
        current_frame -- The frame to replay to.
        rec           -- A game record.
        
        Return value:
        The game state resulting from the rewind and replay or None if 
        no rewind is possible..'''
        rewind = current_frame - auth_state.frame
        if rewind <= 0:
            # The server is ahead of the client. Go to auth_state directly.
            rec.idx = 0
            rec.state[0] = auth_state
            rec.events[0] = []
            return auth_state
        if rewind > rec.size:
            # The state is too old for rewind. Ignore.
            return None
        for i in range(0, rewind):
            self.PlayFrame(auth_state,
                    rec.events[(rec.idx - (rewind - i)) % rec.size])
            pass
        return auth_state
    
    def RewindAndReplayWithKey(self, current_state, frame, evts, rec):
        '''Rewind and replay the game based on an event in the past.

        This method is intended to be used by the server to correct its 
        authoritative state in response to key events sent by the client.

        Arguments:
        current_state -- The game state of the server.
        frame         -- The frame at which the event happened.
        evts          -- A list of events to play at frame.
        rec           -- A game record.

        Return value:
        The game state resulting from the rewind and replay if the rewind 
        was successful, and None otherwise.'''
        rewind = current_state.frame - frame
        if rewind <= 0:
            # The client is ahead of the server. Ignore.
            return None
        if rewind > rec.size:
            # The event is too old to rewind. Ignore.
            # Fix me: We could consider rewinding to the oldest available 
            # frame.
            return None
        # Create a copy of the state to work on so we don't tamper with the 
        # record. 
        s = copy.deepcopy(rec.state[(rec.idx - rewind) % rec.size])
        self.PlayFrame(s, evts)
        for i in range(0, rewind):
            self.PlayFrame(s, rec.evts[(rec.idx - rewind + i) % rec.size])
            pass
        return s

    def CreateGame(self):
        '''Create the initial game state.

        To do: Add arguments to configure the game.

        Return value:
        The initial game state.'''
        buffer_region = 50
        ball_wall_offset_x = 8
        ball_wall_offset_y = 40
        paddle_offset = 60
        paddle_half_width = 8
        paddle_half_height = 30
        s = GameState()
        # The number of players.
        s.player_size = 3
        s.game_length = 60.0
        # the number of rounds (i.e. full rotation of roles) per game
        s.rounds = 1
        s.round_length = s.game_length / s.rounds
        s.rotation_length = s.round_length / s.player_size
        s.frames_per_sec = 60.0
        s.sec_per_frame = 1 / s.frames_per_sec
        s.screen.half_width = 320
        s.screen.half_height = 240
        s.goal_left.pos_x = - buffer_region
        s.goal_left.pos_y = s.screen.half_height
        s.goal_left.half_width = buffer_region
        s.goal_left.half_height = 100 *  s.screen.half_height
        s.goal_right.pos_x = 2 * s.screen.half_width + buffer_region
        s.goal_right.pos_y = s.screen.half_height
        s.goal_right.half_width = buffer_region
        s.goal_right.half_height = 100 * s.screen.half_height
        s.ball_wall_top.pos_x = s.screen.half_width
        s.ball_wall_top.pos_y = - buffer_region + ball_wall_offset_y
        s.ball_wall_top.half_width = (s.screen.half_width - paddle_offset -
        paddle_half_width - ball_wall_offset_x)
        s.ball_wall_top.half_height = buffer_region
        s.ball_wall_bottom.pos_x = s.screen.half_width
        s.ball_wall_bottom.pos_y = (2 * s.screen.half_height +  buffer_region -
        ball_wall_offset_y)
        s.ball_wall_bottom.half_width = (s.screen.half_width - paddle_offset -
        paddle_half_width - ball_wall_offset_x)
        s.ball_wall_bottom.half_height = buffer_region
        s.paddle_wall_top.pos_x = s.screen.half_width
        s.paddle_wall_top.pos_y = - buffer_region
        s.paddle_wall_top.half_width = 2 * s.screen.half_width
        s.paddle_wall_top.half_height = buffer_region
        s.paddle_wall_bottom.pos_x = s.screen.half_width
        s.paddle_wall_bottom.pos_y = 2 * s.screen.half_height +  buffer_region
        s.paddle_wall_bottom.half_width = 2 * s.screen.half_width
        s.paddle_wall_bottom.half_height = buffer_region
        s.ball.pos_x = s.screen.half_width
        s.ball.pos_y = s.screen.half_height
        s.ball.vel_x = -4
        s.ball.vel_y = 0
        s.ball.half_width = 2
        s.ball.half_height = 2
        s.paddle_left.pos_x = paddle_offset
        s.paddle_left.pos_y = 0
        s.paddle_left.vel_x = 0
        s.paddle_left.vel_y = 0
        s.paddle_left.half_width = paddle_half_width
        s.paddle_left.half_height = paddle_half_height
        s.paddle_right.pos_x = 2 * s.screen.half_width - paddle_offset 
        s.paddle_right.pos_y = 0
        s.paddle_right.vel_x = 0
        s.paddle_right.vel_y = 0
        s.paddle_right.half_width = paddle_half_width
        s.paddle_right.half_height = paddle_half_height
        # scores[p] is the score for player p.
        s.scores = [0, 0, 0]
        # roles[p] is the current role of player p.
        s.roles = [GameState.ROLE_LEFT_PADDLE, GameState.ROLE_RIGHT_PADDLE,
                GameState.ROLE_BALL]
        # players[r] is the ID of the player with role r.
        s.players = [0, 0, 1, 2]
        s.start_time = time.time()
        return s

    def RunGame(self, s, rec, r, timeout):
        '''Run the game.

        Arguments:
        s       -- The game state to run the game from.
        rec     -- The game record for saving state and events.
        r       -- The renderer.
        timeout -- The amount of time to run the game.'''
        start_time = time.time()
        while True:
            s.frame_start = time.time()
            if s.frame_start - start_time >= timeout:
                break
            evts = self.GetEvents(s)
            # to do: send events
            self.PlayFrame(s, evts)
            rec.AddEntry(s, evts)
            r.RenderAll(s)
            delta = time.time() - s.frame_start
            if 0 < delta and delta < s.sec_per_frame:
                time.sleep(s.sec_per_frame - delta)
            pass
        pass
    pass

    def PlayRotation(self, s, rec, r):
        '''Play one rotation of the game.

        Argument:
        s -- The game state to start the rotation from.'''

        logger.debug('starting rotation')
        self.RunGame(s, rec, r, s.rotation_length)

    def PlayRound(self, s, rec, r):
        '''Play one round of the game, with each player playing every role.

        Argument:
        s -- The game state to start the round from.'''

        logger.debug('starting round')
        for i in range(0, s.player_size):
            self.PlayRotation(s, rec, r)
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
        s = self.CreateGame()
        rec = GameRecord()
        # Pick an estimate for a value greater than 2L. We won't bother 
        #  measuring it. 360 frames -> 6 seconds at 60 FPS should be more than 
        # enough for a decent connection, and the player wouldn't want to play 
        # on anything worse.
        rec.SetSize(360)
        r = Renderer()
        r.Init()
        #e.RunGame(s, rec, r, 10)
        for i in range(0, s.rounds):
            self.PlayRound(s, rec, r)
            pass
        pass

if __name__ == '__main__':
    e = GameEngine()
    e.Play()
    pass
