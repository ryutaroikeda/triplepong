import cProfile
import os
import sys
sys.path.append(os.path.abspath('src'))
from engine import GameEngine
from gamestate import GameState
def ProfilePlayFrame():
    e = GameEngine()
    s = GameState()
    for i in range(0, 150000):
        e.PlayFrame(s, 0)

if __name__ == '__main__':
    cProfile.run('ProfilePlayFrame()')


