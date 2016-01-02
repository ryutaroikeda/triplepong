#! /usr/bin/env python3
if __name__ == '__main__':
    import cProfile
    import unittest
    s = unittest.TestLoader().discover('..', pattern='*_test.py')
    def run_tests():
        unittest.TextTestRunner().run(s)
    s = cProfile.run('run_tests()',sort='cumtime')
