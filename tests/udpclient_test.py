import os
import sys
import unittest
sys.path.append(os.path.abspath('src'))
from engine import GameEngine
from gamerecord import GameRecord
from gamestate import GameState
from udpclient import UDPClient
from udpeventsocket import UDPEventSocket
from udpsocket import UDPSocket
class UDPClientTest(unittest.TestCase):
    def template_ShouldApplyStateUpdate(self, unacked_1, unacked_2, 
            frame, update_frame, update_history, size, expected_unacked_1, 
            expected_unacked_2, expected_answer):
        c = UDPClient()
        c.unacked_1 = unacked_1
        c.unacked_2 = unacked_2
        e = GameEngine()
        answer = c.ShouldApplyStateUpdate(e, frame, update_frame,
                update_history, size)
        self.assertTrue(c.unacked_1 == expected_unacked_1)
        self.assertTrue(c.unacked_2 == expected_unacked_2)
        self.assertTrue(answer == expected_answer)

    def test_ShouldApplyStateUpdate_1(self):
        self.template_ShouldApplyStateUpdate(-1, -1, 1, 
                0, int('0'*64,2), 64, -1 ,-1, 1)

    def test_ShouldApplyStateUpdate_2(self):
        self.template_ShouldApplyStateUpdate(0, -1, 2, 
                1, int('0'*63+'1',2), 64, -1, -1, 1)

    def test_ShouldApplyStateUpdate_3(self):
        '''Unacked and triggered.'''
        self.template_ShouldApplyStateUpdate(0, -1, 0,
                0, int('0'*64,2), 64, 0, -1, 0)

    def test_ShouldApplyStateUpdate_4(self):
        '''Lost unacked event.'''
        self.template_ShouldApplyStateUpdate(0, -1, 64,
                65, int('1'*64,2), 64, -1, -1, 2)

    def test_ShouldApplyStateUpdate_5(self):
        '''Unacked and untriggered.'''
        self.template_ShouldApplyStateUpdate(32, -1, 31,
                30, int('0'*64,2), 64, 32, -1, 1)

    def test_ShouldApplyStateUpdate_6(self):
        '''Ignore future update.'''
        self.template_ShouldApplyStateUpdate(-1, -1, 0,
                64, int('1'*64,2), 64, -1, -1, 0)

