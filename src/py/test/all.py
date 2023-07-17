# python3 src/py/test/all.py 
import unittest

if __name__ == "__main__":

    loader = unittest.TestLoader()
    start_dir = 'src/py/test/'
    suite = loader.discover(start_dir)

    runner = unittest.TextTestRunner()
    runner.run(suite)