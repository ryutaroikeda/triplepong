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
    def __init__(self):
        pass

    def GetEvents(self):
        '''Return a list of events to apply.

        Return value:
        The list of events that should be applied to the current frame. Each 
        event is a value defined in GameEvent (see ApplyEvents() and 
        gameevent.py).

        To do: Use EventQueue and move the keyboard event getter elsewhere.
        To do: Allow user to configure key bindings.'''
        evts = []
        # Events should be pumped before calling get_pressed(). These functions 
        # are wrappers for SDL functions intended to be used in this way.
        # See https://www.pygame.org/docs/ref/
        # key.html#comment_pygame_key_get_pressed
        pygame.event.pump()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            evts.append(GameEvent.EVENT_FLAP_LEFT_PADDLE)
            pass
        return evts

    def RecordKeyEvent(self, s, evt):
        '''Record that event evt happened at the current frame.
        
        Arguments:
        s   -- The current game state.
        evt -- The event to record.'''
        raise NotImplementedError

    def ApplyGravity(self, s):
        '''Apply gravity to the paddles and the ball

        Arguments:
        s -- the game state'''

        if s.paddle_left.vel_y < 16:
            s.paddle_left.vel_y += 1
            pass
        if s.paddle_right.vel_y < 16:
            s.paddle_right.vel_y += 1
            pass
        if s.ball.vel_y < 16:
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

        for e in evts:
            if e == GameEvent.EVENT_FLAP_LEFT_PADDLE:
                s.paddle_left.vel_y = -8
                pass
            if e == GameEvent.EVENT_FLAP_RIGHT_PADDLE:
                s.paddle_right.vel_y = -8
                pass
            if e == GameEvent.EVENT_FLAP_BALL:
                s.ball.vel_y = -4
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
        '''Rewind and replay the game.

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

    def Run(self):
        s = GameState()
        s.game_length = 9.0
        s.sessionlength = s.game_length / 3
        # the number of rounds (i.e. rotation of roles) per game
        s.rounds = 1
        s.frames_per_sec = 30.0
        s.sec_per_frame = 1 / s.frames_per_sec
        s.screen.half_width = 320
        s.screen.half_height = 240
        buffer_region = 50
        s.goal_left.pos_x = - buffer_region
        s.goal_left.pos_y = s.screen.half_height
        s.goal_left.half_width = buffer_region
        s.goal_left.half_height = 100 *  s.screen.half_height
        s.goal_right.pos_x = 2 * s.screen.half_width + buffer_region
        s.goal_right.pos_y = s.screen.half_height
        s.goal_right.half_width = buffer_region
        s.goal_right.half_height = 100 * s.screen.half_height
        s.ball_wall_top.pos_x = s.screen.half_width
        s.ball_wall_top.pos_y = - buffer_region
        s.ball_wall_top.half_width = s.screen.half_width
        s.ball_wall_top.half_height = buffer_region
        s.ball_wall_bottom.pos_x = s.screen.half_width
        s.ball_wall_bottom.pos_y = 2 * s.screen.half_height +  buffer_region
        s.ball_wall_bottom.half_width = s.screen.half_width
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
        s.paddle_left.pos_x = 60
        s.paddle_left.pos_y = 0
        s.paddle_left.vel_x = 0
        s.paddle_left.vel_y = 0
        s.paddle_left.half_width = 10
        s.paddle_left.half_height = 60 
        s.paddle_right.pos_x = 2 * s.screen.half_width - 60
        s.paddle_right.pos_y = 0
        s.paddle_right.vel_x = 0
        s.paddle_right.vel_y = 0
        s.paddle_right.half_width = 10
        s.paddle_right.half_height = 60
        # scores[p] is the score for player p.
        s.scores = [0, 0, 0]
        # roles[p] is the current role of player p.
        s.roles = [GameState.ROLE_LEFT_PADDLE, GameState.ROLE_RIGHT_PADDLE,
                GameState.ROLE_BALL]
        # players[r] is the ID of the player with role r.
        s.players = [0, 1, 2]
        s.start_time = time.time()
        r = Renderer()
        r.Init()
        while True:
            s.frame_start = time.time()
            if s.frame_start - s.start_time >= s.game_length:
                break
            evts = self.GetEvents()
            self.PlayFrame(s, evts)
            r.RenderAll(s)
            pass
        pass
    pass

if __name__ == '__main__':
    e = GameEngine()
    e.Run()
    pass
