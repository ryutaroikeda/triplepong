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
from gamerecord import GameRecord
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
        self.is_client = False
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
        evt = svr.ReadEvent()
        if evt != None:
            logger.debug('received update {0}'.format(evt.frame))
        return evt

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
                logger.debug('unreading future event')
                c.UnreadEvent()
                continue
            evts.append(evt)
            logger.debug('received key event {0}'.format(evt.frame))
            pass
        return evts

    def SendStateUpdate(self, clients, s):
        '''Send a partial state to the connected sockets in clients.

        Arguments:
        clients -- The clients to send to.
        s      -- The game state to send.'''
        logger.debug('sending state update {0}'.format(s.frame))
        for c in clients:
            c.WriteEvent(s)
        pass

    def SendKeyboardEvents(self, svr, s, keys):
        '''Serialize a game event and send to the server.

        Arguments:
        svr  -- The server socket to send to.
        s    -- The game state.
        keys -- A flag of game event codes, defined in gameevent.py'''
        if svr == None:
            return
        logger.debug('sending key event {0}'.format(s.frame))
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
        no rewind is possible.
        '''
        rewind = current_frame - auth_state.frame
        if rewind < 0:
            # The server is ahead of the client. Go to auth_state directly.
            rec.available = 0
            logger.debug('jumping to auth state')
            return auth_state
        if rewind > rec.available:
            # The state is too old for rewind.
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
        all later states up to s.frame.

        s is set to the result of the rewind.

        Arguments:
        s             -- The game state of the server.
        evt           -- A game event to play.
        rec           -- A game record.

        '''
        rewind = s.frame - evt.frame
        if rewind < 0:
            # The client is ahead of the server. Ignore.
            # This should never happen if we are unreading events in
            # the method GetClientEvents().
            logger.debug('client is ahead - ignoring')
            return None
        if rewind > rec.available:
            # The event is too old to rewind. Ignore the event.
            # fix me:
            # The client needs to know the event was ignored, so return 
            # the previous frame?
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
            pass
        rec.states[rec.idx].Copy(s)
        # reset key_flags (some tests rely on this feature).
        s.key_flags = 0
        return s

    def RunFrameAsClient(self, s, rec):
        '''The main loop of the client.

        The client checks for updates from the server. If there isn't an update 
        available, the client plays a frame with the keys obtained from the 
        keyboard.

        If there is an update, it applies the rewind-replay. If the update 
        is for the current frame, the key_flags are added to those from the 
        keyboard. Then the frame is played.

        '''
        update = None
        keys = self.GetKeyboardEvents(s)
        # Send local key events.
        if keys != 0:
            self.SendKeyboardEvents(self.server, s, keys)
        update = self.GetServerEvent(self.server)
        if update != None:
            # if the update is for the current frame, set the keys.
            if update.frame == s.frame:
                keys |= update.key_flags
            update = self.RewindAndReplayWithState(update, s.frame, rec)
            # if update is None, we should ignore it. Otherwise, update.
            if update != None:
                update.Copy(s)
            pass
        rec.AddEntry(s, keys)
        self.PlayFrame(s, keys)
        self.renderer.RenderAll(s)
        pass

    def RunFrameAsServer(self, s, rec):
        '''The main loop of the server.

        The server first checks for events from the clients. If there isn't an 
        event available, the server plays a frame.
        
        If there is an event, it applies the rewind-replay for correction.
        The corrected state, along with any key events in the current frame,
        are sent to each client. Finally, the current frame is played.

        '''
        s.key_flags = 0
        keys = 0
        key_evts = self.GetClientEvents(self.clients, s.frame)
        # Amend the game record.
        applied_evts = []
        for evt in key_evts:
            if evt.frame == s.frame:
               keys |= evt.keys
            # Update the record with the new event, if applicable.
            if rec.ApplyEvent(s.frame, evt) == 0:
                applied_evts.append(evt)
            pass
        if len(applied_evts) > 0:
            # Sort the events by frame.
            sorted(applied_evts, key=lambda x: x.frame, reverse=False)
            # Call rewind using the earliest applicable event.
            evt = key_evts[0]
            self.RewindAndReplayWithKey(s, evt, rec)
            # Send state to clients.
            s.key_flags = keys
            self.SendStateUpdate(self.clients, s)
        pass
        rec.AddEntry(s, keys)
        self.PlayFrame(s, keys)
        self.renderer.RenderAll(s)
        pass

    def RunGame(self, s, rec, max_frame, frame_rate):
        '''Run the game.

        This is the main game loop.

        Arguments:
        s       -- The game state to run the game from.
        rec     -- The game record for saving state and events.
        max_frame -- The number of frames to run the game for.
        frame_rate -- The number of frames to play per second.
        '''
        start_time = time.time()
        start_frame = s.frame
        end_frame = start_frame + max_frame
        while True:
            if s.frame >= end_frame:
                break
            # Compute the target current frame.
            target_frame = int(((time.time() - start_time) * frame_rate))
            if target_frame > end_frame:
                target_frame = end_frame
            # Loop here until we catch up.
            while s.frame < target_frame:
                if self.is_client:
                    self.RunFrameAsClient(s, rec)
                elif self.is_server:
                    self.RunFrameAsServer(s, rec)
                else:
                    # This feature is used for testing.
                    rec.AddEntry(s, 0)
                    self.PlayFrame(s, 0)
                pass
        pass

    def RotateRoles(self, s):
        '''Rotate the roles of the players.
        Argument:
        s -- The game state.
        '''
        tmp = s.roles[1:]
        tmp.append(s.roles[0])
        s.roles = tmp
        for player_id in range(0, len(s.roles)):
            s.players[s.roles[player_id]] = player_id

    def PlayRound(self, s, rec, rotations, rotation_length, frame_rate):
        '''Play one round of the game, with each player playing every role.

        Argument:
        s -- The game state to start the round from.
        rotations -- The number of rotations in the round.
        rec -- The game record to record the game on.
        rotation_length -- The number of frames to play for each rotation.
        frame_rate -- The number of frames to play per second.
        '''

        logger.debug('starting round')
        for i in range(0, rotations):
            logger.debug('starting rotation')
            self.RunGame(s, rec, rotation_length, frame_rate)
            self.RotateRoles(s)

    def Play(self):
        s = GameState()
        rec = GameRecord()
        # Pick an estimate for a value greater than 2L.
        rec.SetSize(int(s.frames_per_sec) * 5)
        rotation_length = s.rotation_length
        for i in range(0, s.rounds):
            self.PlayRound(s, rec, s.player_size, rotation_length, 
                    s.frames_per_sec)
            pass
        # To do: The server sends an end of game message to each client.

if __name__ == '__main__':
    e = GameEngine()
    e.is_client = True
    e.is_server = False
    from renderer import Renderer
    r = Renderer()
    r.Init()
    e.renderer = r
    e.keyboard = r
    e.Play()
    pass
