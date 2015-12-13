import os
import pygame
import sys
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
    screen_height -- The height of the screen.'''

    def __init__(self):
        self.screen_width = 640
        self.screen_height = 480
        self.surface = None
        self.font = None
        self.font_size = 24
        pass
    def GetRect(self, obj):
        '''Returns a tuple (x, y, w, h) representing a rect from the given 
        GameObject.'''
        return (obj.pos_x - obj.half_width, obj.pos_y - obj.half_height,
                2 * obj.half_width, 2 * obj.half_height)
    def RenderBackground(self, surface):
        '''Fills the background with one color.'''

        pygame.draw.rect(surface, (0, 0, 0),
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
                    (255, 255, 255))
            surface.blit(score, pos)
            pass

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
        pygame.draw.rect(surface, (255, 255, 255), paddle_left)
        pygame.draw.rect(surface, (255, 255, 255), paddle_right)
        pygame.draw.rect(surface, (255, 255, 255), ball)
        pygame.draw.rect(surface, (255, 255, 255), ball_wall_top)
        pygame.draw.rect(surface, (255, 255, 255), ball_wall_bottom)
        pass
    def RenderAll(self, state):
        '''Render the screen.
        
        Argument:
        state -- The game state to render.'''

        self.RenderBackground(self.surface)
        self.RenderScore(self.surface, state)
        self.RenderState(self.surface, state)
        pygame.display.flip()
        pass
    def GetKeys(self):
        '''Get the keyboard state.'''
        # Events should be pumped before calling get_pressed(). These functions 
        # are wrappers for SDL functions intended to be used in this way.
        # See https://www.pygame.org/docs/ref/
        # key.html#comment_pygame_key_get_pressed
        pygame.event.pump()
        return pygame.key.get_pressed()

    def Init(self):
        '''Initialize the renderer. This must be called before use.'''

        pygame.init()
        pygame.display.set_mode((640, 480))
        self.surface = pygame.display.get_surface()
        self.font = pygame.font.Font(None, self.font_size)
        pass
    def Run(self):
        '''To do: Use this to run the renderer as a separate process.
        This is not important now.'''

        pygame.init()
        pygame.display.set_mode((640, 480))
        #
        pygame.quit()
        pass
    pass
