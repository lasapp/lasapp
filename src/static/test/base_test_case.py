import unittest

class BaseTestCase(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.test_path = "tmp/tmp_test_file"

    def write_program(self, program_text, language):
        ending = {"julia": ".jl", "python": ".py"}[language]
        path = self.test_path + ending
        with open(path, "w") as f:
            f.write(program_text)
        return path