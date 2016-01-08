#!/usr/bin/env python
# -*- coding: utf-8 -*-
import copy
import logging
import multiprocessing
import os
import select
import sys
import time
sys.path.append(os.path.abspath('src'))
from bitrecord import BitRecord
from eventtype import EventType
from eventsocket import EventSocket
from endgameevent import EndGameEvent
from gameconfig import GameConfig
from gameobject import GameObject
from gamestate import GameState
from gameevent import GameEvent
from gamerecord import GameRecord
from nullrenderer import NullRenderer
from nullkeyboard import NullKeyboard
import tpsocket
import tplogger
logger = tplogger.getTPLogger('udpgameengine.log', logging.DEBUG)

class UDPGameEngine(object):
    '''This class contains the logic for running the game.

    To play the game, define an object that implements PlayFrames and 
    PrintStats and call PlayAs() from the engine.

    Attributes:
    state              -- The GameState.
    renderer           -- The renderer to use. 
    keyboard           -- The keyboard to get input from. 
    rec                -- The GameRecord.
    bitrec             -- The BitRecord.
    key_cool_down_time -- The minimum frame between game events for each player.
    player_id          -- The player ID of the client.
    is_client          -- True if this is running as a client.
    is_server          -- True if this is running as the server.
    clients            -- The list of client sockets.
    server             -- The socket connected to the server.
    buffer_delay       -- The number of frames of delay to apply to key events.
    buffered_frame_1   
    buffered_frame_2   -- The frame of event buffered during delay or cool-down     
    buffer_size        -- The size of the game state buffer.
    should_apply_gravity   -- Enable gravity.
    should_apply_collision -- Enable collision detection and handling.
    paddle_flap_vel    -- The amount of paddle 'flap'.
    ball_flap_vel      -- The amount of ball 'flap'.
    post_game_time     -- Time in seconds to run engine after end of game.
    '''

    K_SPACE = 32
    def __init__(self):
        self.state = GameState()
        self.renderer = NullRenderer()
        self.keyboard = NullKeyboard()
        self.rec = GameRecord()
        self.bitrec = BitRecord()
        self.key_cool_down_time = 10
        self.player_id = 0
        self.is_client = False
        self.is_server = False
        self.clients = []
        self.server = None
        self.buffer_delay = 0
        self.buffered_frame_1 = -1
        self.buffered_frame_2 = -1
        self.buffer_size = 64
        self.should_apply_gravity = True
        self.should_apply_collision = True
        self.paddle_flap_vel = -12
        self.ball_flap_vel = -8
        self.post_game_time = 30

    def RoleToEvent(self, role):
        '''Convert role into its corresponding game event.
        '''
        if role == GameState.ROLE_LEFT_PADDLE:
            return GameEvent.EVENT_FLAP_LEFT_PADDLE
        elif role == GameState.ROLE_RIGHT_PADDLE:
            return GameEvent.EVENT_FLAP_RIGHT_PADDLE
        elif role == GameState.ROLE_BALL:
            return GameEvent.EVENT_FLAP_BALL
        return GameEvent.EVENT_NO_OP

    def EndGame(self, s):
        s.should_render_score = True
        s.should_render_crown = False
        s.is_ended = True

    def HandleEndGameEvent(self, s, evt):
        s.scores[0] = evt.score_0
        s.scores[1] = evt.score_1
        s.scores[2] = evt.score_2
        self.EndGame(s)

    def SendEndGameEvent(self, clients, s):
        '''Send the end of game event to each client.
        Arguments:
        clients -- The list of client EventSocket.
        s       -- The game state.
        '''
        evt = EndGameEvent()
        evt.score_0 = s.scores[0]
        evt.score_1 = s.scores[1]
        evt.score_2 = s.scores[2]
        for c in list(clients):
            try:
                c.WriteEvent(evt)
            except Exception as e:
                logger.exception(e)
                c.Close()
                clients.remove(c)

    def ApplyGravity(self, s):
        '''Apply gravity to the paddles and the ball

        Arguments:
        s -- the game state'''
        PADDLE_TERM_VELOCITY = 16
        BALL_TERM_VELOCITY   = 32

        if s.paddle_left.vel_y < PADDLE_TERM_VELOCITY:
            s.paddle_left.vel_y += 1
        if s.paddle_right.vel_y < PADDLE_TERM_VELOCITY:
            s.paddle_right.vel_y += 1
        if s.ball.vel_y < BALL_TERM_VELOCITY:
            s.ball.vel_y += 1

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

        if keys & GameEvent.EVENT_FLAP_LEFT_PADDLE:
            s.paddle_left.vel_y = self.paddle_flap_vel
        if keys & GameEvent.EVENT_FLAP_RIGHT_PADDLE:
            s.paddle_right.vel_y = self.paddle_flap_vel
        if keys & GameEvent.EVENT_FLAP_BALL:
            s.ball.vel_y = self.ball_flap_vel

    def ApplyLogic(self, s):
        '''Update positions.
        
        Arguments:
            s    -- the state of the game.
        '''
        s.ball.pos_x += s.ball.vel_x
        s.ball.pos_y += s.ball.vel_y
        s.paddle_left.pos_y += s.paddle_left.vel_y
        s.paddle_right.pos_y += s.paddle_right.vel_y

    def ApplyCollision(self, s):
        '''
        Handle collisions.
        '''
        if s.paddle_left.IsCollidingWith(s.ball):
            s.paddle_left.AlignRight(s.ball)
            s.ball.vel_x = - s.ball.vel_x
            
        if s.paddle_right.IsCollidingWith(s.ball):
            s.paddle_right.AlignLeft(s.ball)
            s.ball.vel_x = - s.ball.vel_x
            
        if s.ball.IsCollidingWith(s.ball_wall_top):
            s.ball_wall_top.AlignBottom(s.ball)
            s.ball.vel_y = - s.ball.vel_y
            
        if s.ball.IsCollidingWith(s.ball_wall_bottom):
            s.ball_wall_bottom.AlignTop(s.ball)
            s.ball.vel_y = - s.ball.vel_y
            
        if s.paddle_left.IsCollidingWith(s.paddle_wall_top):
            s.paddle_wall_top.AlignBottom(s.paddle_left)
            s.paddle_left.vel_y = - s.paddle_left.vel_y
            
        if s.paddle_right.IsCollidingWith(s.paddle_wall_top):
            s.paddle_wall_top.AlignBottom(s.paddle_right)
            s.paddle_right.vel_y = - s.paddle_right.vel_y
            
        if s.paddle_left.IsCollidingWith(s.paddle_wall_bottom):
            s.paddle_wall_bottom.AlignTop(s.paddle_left)
            s.paddle_left.vel_y = - s.paddle_left.vel_y
            
        if s.paddle_right.IsCollidingWith(s.paddle_wall_bottom):
            s.paddle_wall_bottom.AlignTop(s.paddle_right)
            s.paddle_right.vel_y = - s.paddle_right.vel_y
            
        if s.ball.IsCollidingWith(s.goal_left):
            s.ball.pos_x = ( s.goal_right.pos_x + s.goal_left.pos_x ) // 2
            s.ball.pos_y = ( s.ball_wall_top.pos_y +
                    s.ball_wall_bottom.pos_y ) // 2
            s.ball.vel_x = - s.ball.vel_x
            s.ball.vel_y = 0
            
        if s.ball.IsCollidingWith(s.goal_right):
            s.ball.pos_x = ( s.goal_right.pos_x + s.goal_left.pos_x ) // 2
            s.ball.pos_y = ( s.ball_wall_top.pos_y +
                    s.ball_wall_bottom.pos_y ) // 2
            s.ball.vel_x = - s.ball.vel_x
            s.ball.vel_y = 0

    def ApplyScoring(self, s, bitrec):
        if self.GetBit(bitrec.bits[4], s.frame % self.buffer_size):
            return 1
        if s.ball.IsCollidingWith(s.goal_left):
            s.scores[s.players[GameState.ROLE_BALL]] += 1
            bitrec.bits[4] = self.SetBit(bitrec.bits[4],
                    s.frame % self.buffer_size, 1, self.buffer_size)
            
        if s.ball.IsCollidingWith(s.goal_right):
            s.scores[s.players[GameState.ROLE_BALL]] += 1
            bitrec.bits[4] = self.SetBit(bitrec.bits[4],
                    s.frame % self.buffer_size, 1, self.buffer_size)
        return 0

    def PlayFrame(self, s, keys, bitrec):
        '''Move the game forward by one frame.

        Arguments:
        s    -- The game state.
        keys -- The flag for key events.
        bitrec -- Used for score double-count avoidance.
        '''
        if self.should_apply_gravity:
            self.ApplyGravity(s)
        self.ApplyEvents(s, keys)
        self.ApplyLogic(s)
        if not s.is_ended:
            self.ApplyScoring(s, bitrec)
        if self.should_apply_collision:
            self.ApplyCollision(s)
        s.frame += 1
        
    def GetCurrentFrame(self, start_time, frame_rate, now):
        '''Get the frame the server is on.
        Arguments:
        start_time -- Time at the start of game.
        frame_rate -- Frames per second.
        now        -- Current time.
        '''
        assert 0 <= frame_rate
        assert frame_rate <= 32767
        assert start_time <= now
        return int((now - start_time) * frame_rate)

    def RotateBits(self, bits, shift, size):
        '''
        Arguments:
        bits  -- Bits of length size.
        shift -- The bit positions to rotate right by.
        size  -- The length of bits.
        '''
        assert isinstance(shift, int)
        assert isinstance(size, int)
        assert 0 <= bits
        assert 0 <= shift
        assert(shift <= size)
        valmax = 1 << size
        result = (bits >> shift) | ((bits << (size-shift)) % valmax)
        return result

    def UpdateHistory(self, frame, keybits, update_frame, update, size):
        '''
        This method is intended to be used by a peer receiving key input 
        history to update its local state. The history is represented by a
        size-bit integer keybits and a frame number f. 
        The history represents inputs that occurred in frames 
        [f - size, f) excluding f. If g is a frame in this range, the
        (g % size)th bit of the history represents the input at frame g.

        update_frame must be less than or equal to frame.

        Arguments:
        frame        -- The frame associated with keybits.
        keybits      -- size-bits of keys.
        update_frame -- The frame associated with update. This must be
                        older than frame.
        update       -- size-bits of keys.
        size         -- The number of bits in history.

        Return value:
        An updated size-bit history of keys at frame.
        '''
        assert isinstance(size, int)
        assert update_frame <= frame
        # Rotate the oldest frame to the 0th bit.
        rot_keybits = self.RotateBits(keybits, frame % size, size)
        rot_update = self.RotateBits(update, update_frame % size, size)
        result = rot_keybits | (rot_update >> (frame - update_frame))
        return self.RotateBits(result, size - (frame % size), size)

    def BitsToEvent(self, state, bits):
        '''
        Arguments:
        state -- The GameState.
        bits  -- A list of bits, one for each player.

        Return value:
        The GameEvent corresponding to the bits.
        '''
        assert(len(bits) <= 3)
        evt = 0
        for i in range(0, len(bits)):
            evt |= self.RoleToEvent(state.roles[i]) * bits[i]
        return evt

    def SetBit(self, bits, n, b, size):
        '''
        Return value:
        The result of setting the nth bit of bits to b.
        '''
        assert 0 <= n and n < size
        assert b == 0 or b == 1
        x = (bits & (1 << n)) >> n
        return bits ^ ((b ^ x) << n)

    def GetBit(self, bits, n):
        '''
        Returm value:
        Get the nth least significant bit of bits.
        '''
        assert(n >= 0)
        return ((bits & (1 << n)) >> n)

    def IsAcked(self, frame, history, history_frame, size):
        '''
        Arguments:
        frame          -- The frame to check.
        history        -- A size-bit record of key inputs.
        history_frame  -- The frame after the last in history.
        size           -- The size of history.

        Return value:
        True if the bit corresponding to frame in history is 1 and False
        otherwise.
        '''
        assert isinstance(size, int)
        assert frame >= 0
        assert history_frame >= 0
        if frame >= history_frame:
            # Too recent.
            return False
        if history_frame - frame > size:
            # Too old to tell.
            return False
        return self.GetBit(history, frame % size) == 1

    def PlayFromState(self, state, bitrec, rec, play_to, size):
        '''
        Play the game starting at state and using bitrec for events, up to 
        frame play_to. Frames from state.frame inclusive to play_to exclusive
        are put in rec. rec.available is set.

        Arguments:
        state          -- The GameState to play from.
        bitrec         -- The BitRecord of events.
        rec            -- The GameRecord of game states.
        play_to        -- Play up to this frame.
        size           -- The size of bitrec and rec.
        '''
        assert state != None
        assert bitrec != None
        assert rec != None
        #assert isinstance(play_to, (int, long))
        assert isinstance(size, int)
        assert state.frame <= play_to
        assert play_to <= bitrec.frame
        assert state.frame >= bitrec.frame - size
        assert rec.size == size
        start_frame = state.frame
        for i in range(state.frame, play_to):
            n = i % size
            state.Copy(rec.states[n])
            evt = self.BitsToEvent(state, [self.GetBit(bitrec.bits[0], n),
                self.GetBit(bitrec.bits[1], n),
                self.GetBit(bitrec.bits[2], n)])
            self.PlayFrame(state, evt, bitrec)
        rec.available = play_to - start_frame
        assert state.frame == play_to
    
    def PlayFromStateWithPlayer(self, state, bitrec, rec, play_to, player_id,
            size):
        '''During replay, if a frame is flagged, CopyEcceptPlayer() is called.
        '''
        rec.available = play_to - state.frame
        for i in range(state.frame, play_to):
            n = i % size
            if self.GetBit(bitrec.bits[3], n):
                rec.states[n].CopyExceptPlayer(state, state.roles, player_id)
            state.Copy(rec.states[n])
            evt = self.BitsToEvent(state, [self.GetBit(bitrec.bits[0], n),
                self.GetBit(bitrec.bits[1], n),
                self.GetBit(bitrec.bits[2], n)])
            self.PlayFrame(state, evt, bitrec)
        assert state.frame == play_to

    def UpdateBitRecordBit(self, bitrec, frame, history, player_id, size):
        '''
        Update bits for player_id.
        '''
        assert bitrec != None
        assert isinstance(player_id, int)
        assert isinstance(size, int)
        assert frame >= 0
        assert history >= 0
        assert player_id >= 0
        assert player_id < len(bitrec.bits)
        assert size >= 0
        if frame <= bitrec.frame:
            bitrec.bits[player_id] = self.UpdateHistory(bitrec.frame,
                    bitrec.bits[player_id], frame, history, size)
        else:
            bitrec.bits[player_id] = self.UpdateHistory(frame, history,
                    bitrec.frame, bitrec.bits[player_id], size)
            bitrec.frame = frame

    def UpdateBitRecord(self, b1, b2, size):
        '''This does not update flags.'''
        assert b1 != None
        assert b2 != None
        assert isinstance(size, int)
        assert size > 0
        for i in range(0,3):
            self.UpdateBitRecordBit(b1, b2.frame, b2.bits[i], i, size)

    def UpdateBitRecordFrame(self, bitrec, frame, size):
        '''
        Set bitrec.frame to frame and clears old bits to make way for the new.
        '''
        assert bitrec != None
        assert isinstance(size, int)
        assert 0 <= frame
        assert bitrec.frame <= frame
        assert 0 < size
        MAX = 1 << size
        for i in range(0,5):
            r = frame % size
            rot = self.RotateBits(bitrec.bits[i], r, size)
            shift = frame - bitrec.frame
            rot = (rot << shift) % MAX
            bitrec.bits[i] = self.RotateBits(rot, (size - (r - shift)) % size,
                    size)
        bitrec.frame = frame

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

    def PlayAs(self, s, player, start_time):
        '''
        Play the game using player.
        Arguments:
        s          -- The GameState.
        player     -- An object that implements PlayFrames and PrintStats
        '''
        assert s != None
        rotation_length = s.rotation_length
        frame_rate = s.frames_per_sec 
        rounds = s.rounds
        # Busy wait until start time
        while time.time() < start_time:
            pass
        for i in range(0, rounds):
            logger.debug('starting round')
            for i in range(0, 3):
                logger.debug('starting rotation, {0} frames.'.format(
                    rotation_length))
                player.PlayFrames(self, s, float(start_time), rotation_length,
                        frame_rate) 
                self.RotateRoles(s)
        if self.is_server:
            self.SendEndGameEvent(self.clients, s)
        self.EndGame(s)
        player.PrintStats()
        # Keep the game running for a bit, to show the final score.   
        player.PlayFrames(self, s, start_time, 
                frame_rate * self.post_game_time, frame_rate)

    def PlayFrames(self, e, s, start_time, max_frame, frame_rate):
        ''' 
        For testing.
        '''
        self.renderer.Render(s, s, 0, 0)
        time.sleep(5)

    def PrintStats(self):
        pass

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='The triplepong game \
            engine. Use the command line interface for testing.')
    parser.add_argument('-i', '--interpolate', action='store_true',
            default=False, help='Turn on renderer interpolation.')
    args = parser.parse_args()
    e = UDPGameEngine()
    e.is_client = True
    e.is_server = False
    conf = GameConfig()
    conf.do_interpolate = args.interpolate
    conf.Apply(e)
    from renderer import Renderer
    r = Renderer()
    r.Init()
    conf.ApplyRenderer(r)
    e.renderer = r
    e.keyboard = r
    e.PlayAs(e.state, e, 0)
    
