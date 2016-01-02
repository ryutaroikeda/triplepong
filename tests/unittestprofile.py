import cProfile
import unittest

if __name__ == '__main__':
    s = unittest.TestLoader().discover('..', pattern='*_test.py')
    def run_tests():
        unittest.TextTestRunner().run(s)
    s = cProfile.run('run_tests()',sort='cumtime')
