import os
import pygame
import sys
import time
sys.path.append(os.path.abspath('src'))
from gamestate import GameState

class Renderer:
    '''The Renderer renders the game state to the window. It uses pygame.

    To use the renderer r, call r.Init(), then r.RenderAll(s), where s is a 
    game state.

    For the time being, the renderer is also a keyboard. The keyboard state 
    is available with GetKeys().
    
    Attributes:
    screen_width  -- The width of the screen.
    screen_height -- The height of the screen.
    state         -- The state to draw. Used in RenderInterpolated().
    '''

    def __init__(self):
        self.screen_width = 640
        self.screen_height = 480
        self.surface = None
        self.font = None
        self.font_size = 24
        self.crown_font = None
        self.crown_font_size = 64
        self.font_color = (0xFF, 0xFF, 0xFF)
        self.background_color = (0xFF, 0xA9, 0x07)
        self.default_color = (0xFF, 0xCF, 0x74)
        self.your_color = (0xFF, 0xF1, 0xD7)
        self.state = GameState()
        pass
    def GetRect(self, obj):
        '''Returns a tuple (x, y, w, h) representing a rect from the given 
        GameObject.'''
        return (obj.pos_x - obj.half_width, obj.pos_y - obj.half_height,
                2 * obj.half_width, 2 * obj.half_height)
    def RenderBackground(self, surface):
        '''Fills the background with one color.'''

        pygame.draw.rect(surface, self.background_color,
                (0, 0, self.screen_width, self.screen_height))
        pass
    
    def RenderScore(self, surface, state):
        '''Render the score of all players.
        
        The score should be rendered near the top right of each player.
        '''
        if not state.should_render_score:
            return
        for i in range(0, len(state.scores)):
            if state.roles[i] == GameState.ROLE_LEFT_PADDLE:
                pos = state.paddle_left.GetTopRight(self.font_size)
            elif state.roles[i] == GameState.ROLE_RIGHT_PADDLE:
                pos = state.paddle_right.GetTopRight(self.font_size)
            elif state.roles[i] == GameState.ROLE_BALL:
                pos = state.ball.GetTopRight(self.font_size)
            score = self.font.render('{0}'.format(state.scores[i]), 1,
                    self.font_color)
            surface.blit(score, pos)
            pass

    def RenderCrown(self, surface, state):
        '''Render a crown on top of the paddle with the higher score.
        '''
        king = None
        left_score = state.scores[state.players[GameState.ROLE_LEFT_PADDLE]] 
        right_score = state.scores[state.players[GameState.ROLE_RIGHT_PADDLE]]
        is_you = False
        if left_score > right_score:
            king = state.paddle_left
            if state.player_id == state.players[GameState.ROLE_LEFT_PADDLE]:
                is_you = True
        elif left_score < right_score:
            king = state.paddle_right
            if state.player_id == state.players[GameState.ROLE_RIGHT_PADDLE]:
                is_you = True
        if king != None:
            color = self.default_color
            if is_you:
                color = self.your_color
            pos = king.GetTop(self.crown_font_size)
            crown = self.crown_font.render('+', 1, color)
            surface.blit(crown, pos)

    def RenderState(self, surface, state):
        '''Render the game state.

        Arguments:
        surface -- The pygame surface to render to.
        state   -- The game state to render.'''

        paddle_left = self.GetRect(state.paddle_left)
        paddle_right = self.GetRect(state.paddle_right)
        ball = self.GetRect(state.ball)
        ball_wall_top = self.GetRect(state.ball_wall_top)
        ball_wall_bottom = self.GetRect(state.ball_wall_bottom)
        default_color = self.default_color
        pygame.draw.rect(surface, default_color, paddle_left)
        pygame.draw.rect(surface, default_color, paddle_right)
        pygame.draw.rect(surface, default_color, ball)
        pygame.draw.rect(surface, default_color, ball_wall_top)
        pygame.draw.rect(surface, default_color, ball_wall_bottom)
        your_color = self.your_color
        if state.roles[state.player_id] == GameState.ROLE_LEFT_PADDLE:
            pygame.draw.rect(surface, your_color, paddle_left)
        if state.roles[state.player_id] == GameState.ROLE_RIGHT_PADDLE:
            pygame.draw.rect(surface, your_color, paddle_right)
        if state.roles[state.player_id] == GameState.ROLE_BALL:
            pygame.draw.rect(surface, your_color, ball)
        pass

    def RenderAll(self, state):
        '''Render the screen.
        
        Argument:
        state -- The game state to render.'''
        self.RenderBackground(self.surface)
        self.RenderScore(self.surface, state)
        self.RenderCrown(self.surface, state)
        self.RenderState(self.surface, state)
        pygame.display.flip()

    def InterpolateScalar(self, x1, x2, t):
        '''Interpolate x1 and x2 at time t.
        Arguments:
        x1 -- The value at time t = 0.
        x2 -- The value at time t = 1.
        t  -- The time between 0 and 1.
        '''
        return x1 + (x2 - x1) * t

    def InterpolateStates(self, s1, s2, t, result):
        '''Interpolate s1 and s2 at time t into result.
        Arguments:
        s1     -- The state at time t = 0.
        s2     -- The state at time t = 1.
        t      -- The time between 0 and 1.
        result -- A game state.
        '''
        result.paddle_left.pos_y = self.InterpolateScalar( \
                s1.paddle_left.pos_y, s2.paddle_left.pos_y, t)
        result.paddle_right.pos_y = self.InterpolateScalar( \
                s1.paddle_right.pos_y, s2.paddle_right.pos_y, t)
        result.ball.pos_x = self.InterpolateScalar( \
                s1.ball.pos_x, s2.ball.pos_x, t)
        result.ball.pos_y = self.InterpolateScalar( \
                s1.ball.pos_y, s2.ball.pos_y, t)

    def RenderInterpolated(self, prev, state, start_time, end_time):
        '''Render between two states.
        Argument:
        prev    -- The previous state.
        state   -- The current state.
        start_time -- The time in seconds.
        end_time -- The time to stop rendering.
        '''
        delta = end_time - start_time
        if delta <= 0.0:
            return
        self.state.roles = state.roles
        self.state.players = state.players
        self.state.scores = state.scores
        self.state.player_id = state.player_id
        while True:
            t = (time.time() - start_time) / delta
            self.InterpolateStates(prev, state, t, self.state)
            self.RenderAll(self.state)
            if time.time() >= end_time:
                break
        pass

    def GetKeys(self):
        '''Get the keyboard state.'''
        # Events should be pumped before calling get_pressed(). These functions 
        # are wrappers for SDL functions intended to be used in this way.
        # See https://www.pygame.org/docs/ref/
        # key.html#comment_pygame_key_get_pressed
        pygame.event.pump()
        return pygame.key.get_pressed()

    def Init(self, conf):
        '''Initialize the renderer. This must be called before use.
        Argument:
        conf -- The game configuration to use. This is required for setting the 
                positions of immovable objects in .state.
        '''
        conf.ApplyState(self.state)
        pygame.init()
        pygame.display.set_mode((640, 480))
        self.surface = pygame.display.get_surface()
        self.font = pygame.font.Font(None, self.font_size)
        self.crown_font = pygame.font.Font(None, self.crown_font_size)
        pass
    def Run(self):
        '''To do: Use this to run the renderer as a separate process.
        This is not important now.
        '''
        pygame.init()
        pygame.display.set_mode((640, 480))
        #
        pygame.quit()
        pass
    pass
