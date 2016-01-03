import copy
import logging
import os
import socket
import sys
import time
import unittest
sys.path.append(os.path.abspath('src'))
from endgameevent import EndGameEvent
from udpgameengine import UDPGameEngine
from engine import GameRecord
from eventsocket import EventSocket
from gamestate import GameState
from gameevent import GameEvent
import tplogger
logger = tplogger.getTPLogger('engine_test.log', logging.DEBUG)
sys.path.append(os.path.abspath('tests'))
from mockkeyboard import MockKeyboard
from mockeventsocket import MockEventSocket
class UDPGameEngineTest(unittest.TestCase):

    def template_GetCurrentFrame(self, start, frame_rate,
            now, expected_frame):
        e = UDPGameEngine()
        self.assertTrue(e.GetCurrentFrame(start, frame_rate, 
            now) == expected_frame)

    def template_RotateBits(self, bits, shift, size, expected_bits):
        e = UDPGameEngine()
        self.assertTrue(e.RotateBits(bits, shift, size) == expected_bits)

    def template_UpdateHistory(self, frame, keybits, update_frame, 
            update, size, expected_bits):
        e = UDPGameEngine()
        self.assertTrue(e.UpdateHistory(frame,keybits,update_frame,
            update, size) == expected_bits)

    def template_BitsToEvent(self, roles, bits, expected_evt):
        e = UDPGameEngine()
        s = GameState()
        s.roles = roles
        evt = e.BitsToEvent(s, bits)
        self.assertTrue(evt == expected_evt)

    def template_GetBit(self, bits, n, expected_bit):
        e = UDPGameEngine()
        self.assertTrue(e.GetBit(bits, n) == expected_bit)

    def template_SetBit(self, bits, n, b, size, expected_bits):
        e = UDPGameEngine()
        self.assertTrue(e.SetBit(bits, n, b, size) == expected_bits)
    
    def template_IsAcked(self, frame, history, history_frame, size,
            expected_result):
        e = UDPGameEngine()
        result = e.IsAcked(frame, history, history_frame, size) 
        self.assertTrue(result == expected_result)

    def template_UpdateBitRecordBit(self, bits, frame, update, 
            update_frame, size, expected_bits):
        e = UDPGameEngine()
        e.bitrec.bits = bits
        e.bitrec.frame = frame
        e.UpdateBitRecordBit(e.bitrec, update_frame, update, e.player_id,
                size)
        for i in range(0,3):
            self.assertTrue(e.bitrec.bits[i] == expected_bits[i])

    def template_UpdateBitRecordFrame(self, bits, frame, new_frame, size,
            expected_bits):
        e = UDPGameEngine()
        e.bitrec.bits = bits
        e.bitrec.frame = frame
        e.UpdateBitRecordFrame(e.bitrec, new_frame, size)
        self.assertTrue(e.bitrec.bits == expected_bits)
    #UDP stuff END

    def test_init(self):
        e = UDPGameEngine()
        self.assertTrue(e.is_client == False)
        self.assertTrue(e.is_server == False)
        pass

    def test_RoleToEvent(self):
        e = UDPGameEngine()
        self.assertTrue(e.RoleToEvent(GameState.ROLE_LEFT_PADDLE) == \
                GameEvent.EVENT_FLAP_LEFT_PADDLE)
        self.assertTrue(e.RoleToEvent(GameState.ROLE_RIGHT_PADDLE) == \
                GameEvent.EVENT_FLAP_RIGHT_PADDLE)
        self.assertTrue(e.RoleToEvent(GameState.ROLE_BALL) == \
                GameEvent.EVENT_FLAP_BALL)


    def test_HandleEndGameEvent(self):
        e = UDPGameEngine()
        s = GameState()
        evt = EndGameEvent()
        evt.score_0 = 1
        evt.score_1 = 534
        evt.score_2 = -32
        e.HandleEndGameEvent(s, evt)
        self.assertTrue(s.is_ended == True)
        self.assertTrue(s.scores[0] == evt.score_0)
        self.assertTrue(s.scores[1] == evt.score_1)
        self.assertTrue(s.scores[2] == evt.score_2)

    def test_PlayFrame(self):
        '''Test frame count and key_flags in PlayFrame.
        '''
        e = UDPGameEngine()
        s = GameState()
        frame = s.frame
        s.key_flags = GameEvent.EVENT_FLAP_LEFT_PADDLE
        e.PlayFrame(s, s.key_flags, e.bitrec)
        self.assertTrue(s.frame == frame + 1)

    def test_RotateRoles_1(self):
        e = UDPGameEngine()
        s = GameState()
        s.player_size = 1
        s.roles = [GameState.ROLE_LEFT_PADDLE]
        s.players = [-1, 0]
        e.RotateRoles(s)
        self.assertTrue(s.roles == [GameState.ROLE_LEFT_PADDLE])
        self.assertTrue(s.players == [-1, 0])

    def test_RotateRoles_2(self):
        e = UDPGameEngine()
        s = GameState()
        s.player_size = 2
        s.roles = [GameState.ROLE_LEFT_PADDLE, GameState.ROLE_RIGHT_PADDLE]
        s.players = [-1]*(s.player_size + 1)
        s.players[GameState.ROLE_LEFT_PADDLE] = 0
        s.players[GameState.ROLE_RIGHT_PADDLE] = 1
        e.RotateRoles(s)
        self.assertTrue(s.roles == [GameState.ROLE_RIGHT_PADDLE, 
            GameState.ROLE_LEFT_PADDLE])
        self.assertTrue(s.players == [-1, 1, 0])

    def test_RotateRoles_3(self):
        e = UDPGameEngine()
        s = GameState()
        s.roles = [GameState.ROLE_RIGHT_PADDLE, GameState.ROLE_LEFT_PADDLE,
                GameState.ROLE_BALL]
        s.player_size = len(s.roles)
        s.players = [-1]*(len(s.roles)+ 1)
        s.players[GameState.ROLE_LEFT_PADDLE] = 1
        s.players[GameState.ROLE_RIGHT_PADDLE] = 0
        s.players[GameState.ROLE_BALL] = 2
        e.RotateRoles(s)
        self.assertTrue(s.roles == [GameState.ROLE_LEFT_PADDLE,
            GameState.ROLE_BALL, GameState.ROLE_RIGHT_PADDLE])
        players = [-1]*(len(s.roles)+1)
        players[GameState.ROLE_LEFT_PADDLE] = 0
        players[GameState.ROLE_RIGHT_PADDLE] = 2
        players[GameState.ROLE_BALL] = 1
        self.assertTrue(s.players == players)

    def test_EndGame(self):
        e = UDPGameEngine()
        s = GameState()
        e.EndGame(s)
        self.assertTrue(s.is_ended == True)
        self.assertTrue(s.should_render_score == True)

    def test_GetCurrentFrame_1(self):
        self.template_GetCurrentFrame(0,0,0,0)

    def test_GetCurrentFrame_2(self):
        self.template_GetCurrentFrame(0,30,1,30)

    def test_GetCurrentFrame_3(self):
        self.template_GetCurrentFrame(1,30,2,30)

    def test_RotateBits_1(self):
        self.template_RotateBits(int('0000',2), 0, 4, int('0000',2))

    def test_RotateBits_2(self):
        self.template_RotateBits(int('0001',2), 1, 4, int('1000',2))

    def test_RotateBits_3(self):
        self.template_RotateBits(int('0001',2), 2, 4, int('0100',2))

    def test_RotateBits_4(self):
        self.template_RotateBits(int('0001',2), 3, 4, int('0010',2))

    def test_RotateBits_5(self):
        self.template_RotateBits(int('0001',2), 4, 4, int('0001',2))

    def test_RotateBits_6(self):
        self.template_RotateBits(int('00100000',2), 3, 8, int('00000100',2))

    def test_RotateBits_7(self):
        self.template_RotateBits(int('00100000'*2,2), 5, 16, 
                int('00000001'*2,2))

    def test_RotateBits_8(self):
        self.template_RotateBits(int('0001'*8,2), 1, 32, int('1000'*8,2))

    def test_RotateBits_9(self):
        self.template_RotateBits(int('0011'*16,2), 1, 64, int('1001'*16,2))

    def test_UpdateHistory_1(self):
        self.template_UpdateHistory(0,int('0000'*8,2),0,int('0000'*8,2),
                32,int('0000'*8,2))

    def test_UpdateHistory_2(self):
        self.template_UpdateHistory(0,int('0001'*8,2),0,int('1000'*8,2),
                32,int('1001'*8,2))

    def test_UpdateHistory_3(self):
        self.template_UpdateHistory(1,int('0001'*8,2),1,int('1000'*8,2),
                32,int('1001'*8,2))

    def test_UpdateHistory_4(self):
        self.template_UpdateHistory(33,int('0001'*8,2),33,
                int('1000'*8,2), 32,int('1001'*8,2))

    def test_UpdateHistory_5(self):
        self.template_UpdateHistory(33,int('0001'*8,2),0,
                int('1000'*8,2), 32,int('0001'*8,2))

    def test_UpdateHistory_6(self):
        self.template_UpdateHistory(64, int('0100'*8,2),
                32, int('1111'*8,2), 32, int('0100'*8,2))

    def test_UpdateHistory_7(self):
        self.template_UpdateHistory(64,int('0100'*8,2),
                33, int('1111'*8,2), 32,int('0100'*7+'0101',2))

    def test_UpdateHistory_8(self):
        self.template_UpdateHistory(64,int('0100'*8,2),
                34, int('1111'*8,2), 32,int('0100'*7+'0111',2))

    def test_BitsToEvent_1(self):
        self.template_BitsToEvent([GameState.ROLE_LEFT_PADDLE,0,0],
                [1,0,0],GameEvent.EVENT_FLAP_LEFT_PADDLE)

    def test_GetBit_1(self):
        self.template_GetBit(int('0000',2), 0, 0)

    def test_GetBit_2(self):
        self.template_GetBit(int('1000',2), 3, 1)

    def test_SetBit_1(self):
        self.template_SetBit(int('0000',2), 0, 0, 4, int('0000',2))

    def test_SetBit_2(self):
        self.template_SetBit(int('0000', 2), 0, 1, 4, int ('0001',2))

    def test_SetBit_3(self):
        self.template_SetBit(int('0000', 2), 1, 1, 4, int ('0010',2))

    def test_SetBit_4(self):
        self.template_SetBit(int('1111',2), 1, 0, 4, int('1101',2))

    def test_IsAcked_1(self):
        self.template_IsAcked(0, int('0'*64,2), 0, 64, False)

    def test_IsAcked_2(self):
        self.template_IsAcked(0, int('0'*63+'1',2), 1, 64, True)

    def test_IsAcked_3(self):
        self.template_IsAcked(0, int('1'*64,2), 65, 64, False)

    def test_IsAcked_4(self):
        self.template_IsAcked(100, int('0'*27+'1'+'0'*36,2), 150, 64, True)

    def test_UpdateBitRecordBit_1(self):
        self.template_UpdateBitRecordBit([0,0,0],0,0,0,64,[0,0,0])

    def test_UpdateBitRecordBit_2(self):
        self.template_UpdateBitRecordBit([1,1,1],2,8,3,64,[9,1,1])

    def test_UpdateBitRecordBit_3(self):
        self.template_UpdateBitRecordBit([0,0,0],5,int('0'*63+'1',2),10,
                64,[int('0'*63+'1',2),0,0])

    def test_UpdateBitRecordFrame_1(self):
        self.template_UpdateBitRecordFrame([0,0,0,0,0], 0, 0, 64, [0,0,0,0,0])

    def test_UpdateBitRecordFrame_2(self):
        self.template_UpdateBitRecordFrame([1,1,1,0,0],0,0,64,[1,1,1,0,0])

    def test_UpdateBitRecordFrame_3(self):
        self.template_UpdateBitRecordFrame([1,2,1,0,0],64,65,64,[0,2,0,0,0])

    def test_UpdateBitRecordFrame_4(self):
        self.template_UpdateBitRecordFrame([int('1'*64,2),0,0,0,0],100,120,64,
                [int('1'*8+'0'*20+'1'*36,2),0,0,0,0])
