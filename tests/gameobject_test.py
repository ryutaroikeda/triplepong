import os
import sys
import unittest
sys.path.append(os.path.abspath('src'))
from gameobject import GameObject

class GameObjectTest(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass
    def test_IsCollidingWith_1(self):
        a = GameObject()
        b = GameObject()
        a.pos_x = 0
        a.pos_y = 0
        a.half_width = 1
        a.half_height = 1
        b.pos_x = 3
        b.pos_y = 0
        b.half_width = 1
        b.half_height = 1
        self.assertTrue(a.IsCollidingWith(b) == 0)
        self.assertTrue(b.IsCollidingWith(a) == 0)
        pass
    def test_IsCollidingWith_2(self):
        a = GameObject()
        b = GameObject()
        a.pos_x = 0
        a.pos_y = 0
        a.half_width = 1
        a.half_height = 1
        b.pos_x = 0
        b.pos_y = 3
        b.half_width = 1
        b.half_height = 1
        self.assertTrue(a.IsCollidingWith(b) == 0)
        self.assertTrue(b.IsCollidingWith(a) == 0)
        pass
    def test_IsCollidingWith_3(self):
        a = GameObject()
        b = GameObject()
        a.pos_x = 0
        a.pos_y = 0
        a.half_width = 1
        a.half_height = 1
        b.pos_x = 2
        b.pos_y = 0
        b.half_width = 1
        b.half_height = 1
        self.assertTrue(a.IsCollidingWith(b) == 1)
        self.assertTrue(b.IsCollidingWith(a) == 1)
        pass
    def test_IsCollidingWith_4(self):
        a = GameObject()
        b = GameObject()
        a.pos_x = 0
        a.pos_y = 0
        a.half_width = 1
        a.half_height = 1
        b.pos_x = 0
        b.pos_y = 2
        b.half_width = 1
        b.half_height = 1
        self.assertTrue(a.IsCollidingWith(b) == 1)
        self.assertTrue(b.IsCollidingWith(a) == 1)
        pass
    def test_IsCollidingWith_5(self):
        a = GameObject()
        b = GameObject()
        a.pos_x = 0
        a.pos_y = 0
        a.half_width = 1
        a.half_height = 1
        b.pos_x = 1
        b.pos_y = 0
        b.half_width = 1
        b.half_height = 1
        self.assertTrue(a.IsCollidingWith(b) == 1)
        self.assertTrue(b.IsCollidingWith(a) == 1)
        pass
    def test_IsCollidingWith_6(self):
        a = GameObject()
        b = GameObject()
        a.pos_x = 0
        a.pos_y = 0
        a.half_width = 1
        a.half_height = 1
        b.pos_x = 1
        b.pos_y = 1
        b.half_width = 1
        b.half_height = 1
        self.assertTrue(a.IsCollidingWith(b) == 1)
        self.assertTrue(b.IsCollidingWith(a) == 1)
        pass
    def test_IsCollidingWith_7(self):
        a = GameObject()
        b = GameObject()
        a.pos_x = 0
        a.pos_y = 0
        a.half_width = 1
        a.half_height = 1
        b.pos_x = 0
        b.pos_y = 1
        b.half_width = 1
        b.half_height = 1
        self.assertTrue(a.IsCollidingWith(b) == 1)
        self.assertTrue(b.IsCollidingWith(a) == 1)
        pass
    def test_IsCollidingWith_8(self):
        a = GameObject()
        b = GameObject()
        a.pos_x = 0
        a.pos_y = 0
        a.half_width = 1
        a.half_height = 1
        b.pos_x = 2
        b.pos_y = 0
        b.half_width = 2
        b.half_height = 0.5
        self.assertTrue(a.IsCollidingWith(b) == 1)
        self.assertTrue(b.IsCollidingWith(a) == 1)
        pass
    def test_IsCollidingWith_9(self):
        a = GameObject()
        b = GameObject()
        a.pos_x = 0
        a.pos_y = 0
        a.half_width = 1
        a.half_height = 1
        b.pos_x = 0.1
        b.pos_y = 0.1
        b.half_width = 2
        b.half_height = 0.5
        self.assertTrue(a.IsCollidingWith(b) == 1)
        self.assertTrue(b.IsCollidingWith(a) == 1)
        pass
    def test_IsCollidingWith_10(self):
        a = GameObject()
        b = GameObject()
        a.pos_x = 0
        a.pos_y = 0
        a.half_width = 1
        a.half_height = 1
        b.pos_x = 0.1
        b.pos_y = 1.1
        b.half_width = 2
        b.half_height = 0.5
        self.assertTrue(a.IsCollidingWith(b) == 1)
        self.assertTrue(b.IsCollidingWith(a) == 1)
        pass
    def test_IsCollidingWith_11(self):
        a = GameObject()
        b = GameObject()
        a.pos_x = 0
        a.pos_y = 0
        a.half_width = 1
        a.half_height = 1
        b.pos_x = 0.1
        b.pos_y = 2.1
        b.half_width = 0.5
        b.half_height = 3
        self.assertTrue(a.IsCollidingWith(b) == 1)
        self.assertTrue(b.IsCollidingWith(a) == 1)
        pass
    def test_IsCollidingWith_12(self):
        a = GameObject()
        b = GameObject()
        a.pos_x = 0
        a.pos_y = 0
        a.half_width = 1
        a.half_height = 1
        b.pos_x = 0.1
        b.pos_y = 0.1
        b.half_width = 0.5
        b.half_height = 0.5
        self.assertTrue(a.IsCollidingWith(b) == 1)
        self.assertTrue(b.IsCollidingWith(a) == 1)
        pass
    
    pass
