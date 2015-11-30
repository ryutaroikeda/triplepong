import os
import pygame
import sys
sys.path.append(os.path.abspath('src'))
from gamestate import GameState

class Renderer:
    def __init__(self):
        self.screen_width = 640
        self.screen_height = 480
        self.surface = None
        pass
    def GetRect(self, obj):
        '''Returns a tuple (x, y, w, h) representing a rect from the given 
        GameObject.'''
        return (obj.pos_x - obj.half_width, obj.pos_y - obj.half_height,
                2 * obj.half_width, 2 * obj.half_height)
    def RenderBackground(self, surface):
        pygame.draw.rect(surface, (0, 0, 0),
                (0, 0, self.screen_width, self.screen_height))
        pass
    def RenderScore(self, surface, state):
        pass
    def RenderState(self, surface, state):
        paddle_left = self.GetRect(state.paddle_left)
        paddle_right = self.GetRect(state.paddle_right)
        ball = self.GetRect(state.ball)
        pygame.draw.rect(surface, (255, 255, 255), paddle_left)
        pygame.draw.rect(surface, (255, 255, 255), paddle_right)
        pygame.draw.rect(surface, (255, 255, 255), ball)
        pass
    def RenderAll(self, state):
        self.RenderBackground(self.surface)
        self.RenderScore(self.surface, state)
        self.RenderState(self.surface, state)
        pygame.display.flip()
        pass
    def Init(self):
        pygame.init()
        pygame.display.set_mode((640, 480))
        self.surface = pygame.display.get_surface()
        pass
    def Run(self):
        pygame.init()
        pygame.display.set_mode((640, 480))
        #
        pygame.quit()
        pass
    pass
