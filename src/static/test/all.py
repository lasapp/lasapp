# python3 src/static/test/all.py

import unittest
from pathlib import Path

if __name__ == "__main__":
    Path("./tmp").mkdir(exist_ok=True)

    loader = unittest.TestLoader()
    start_dir = 'src/static/test/'
    suite = loader.discover(start_dir)

    runner = unittest.TextTestRunner()
    runner.run(suite)