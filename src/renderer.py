import os
import pygame
import sys
sys.path.append(os.path.abspath('src'))
from gamestate import GameState

class Renderer:
    def __init__(self):
        self.screen_width = 640
        self.screen_height = 480
        pass
    def GetRect(pos_x, pos_y, half_width, half_height):
        return (pos_x - half_width, pos_y - half_height,
                2 * half_width, 2 * half_height)
    def RenderBackground(self, surface):
        pygame.draw.rect(surface, (255, 255, 255),
                (0, 0, self.screen_width, self.screen_height))
        pass
    def RenderScore(self, surface, state):
        pass
    def RenderState(self, surface, state):
        r1 = self.GetRect(
        pass
    def Run(self):
        pygame.init()
        pygame.display.set_mode((640, 480))
        
        pygame.quit()
        pass
    pass
