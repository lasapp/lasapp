
import unittest
import sys
sys.path.insert(0, 'src/static') # hack for now
from lasapp import ProbabilisticProgram

import os

from base_test_case import BaseTestCase
from analysis.hmc_assumptions_checker import *

class TestHMCAssumptionChecker(BaseTestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)

    def _get_warnings(self, program_text, language):
        path = self.write_program(program_text, language)
        program = ProbabilisticProgram(path)
        warnings = check_hmc_assumptions(program)
        program.close()
        os.remove(path)
        return warnings

    def _test_1(self, program_text, language, variables):
        warnings = self._get_warnings(program_text, language)
        self.assertTrue(
            any(isinstance(warning, MultipleDefinitionsWarning) and warning.random_variable_name == variables["X"] for warning in warnings)
        )
        self.assertTrue(
            any(isinstance(warning, ContinuousDistributionViolation) and warning.random_variable.name == variables["B"] for warning in warnings)
        )
        self.assertTrue(
            sum([isinstance(warning, RandomControlDependentWarning) for warning in warnings]) == 3
        )
        self.assertTrue(
            any(isinstance(warning, MissingInBranchWarning) and warning.random_variable.name == variables["Y"] for warning in warnings)
        )

    def test_1_turing(self):
        program_text = """
using Turing

@model function model()
    B ~ Bernoulli(0.5)
    if B
        X ~ Normal(1., 1.)
    else
        X ~ Normal(-1., 1.)
        Y ~ Normal(-1., 1.)
    end
end
        """
        variables = {"B": "B", "X": "X", "Y": "Y"}
        self._test_1(program_text, "julia", variables)

    def test_1_pyro(self):
        program_text = """
import pyro

def model():
    B = pyro.sample("B", dist.Bernoulli(0.5))
    if B:
        X = pyro.sample("X", dist.Normal(1., 1.))
        Y = pyro.sample("Y", dist.Normal(1., 1.))
    else:
        X = pyro.sample("X", dist.Normal(-1., 1.))
"""
        variables = {"B": "'B'", "X": "'X'", "Y": "'Y'"}
        self._test_1(program_text, "python", variables)


    def _test_2(self, program_text, language, variables):
        warnings = self._get_warnings(program_text, language)
        # print("\n", language, "\n")
        # for warning in warnings:
        #     print(warning)
        
        self.assertTrue(
            any(isinstance(warning, DefinitionInWhileLoopWarning) and warning.random_variable.name == variables["U"] for warning in warnings)
        )

        # self.assertTrue(len(warnings) == 1)
        # self.assertTrue(isinstance(warnings[0], DefinitionInWhileLoopWarning))

    def test_2_turing(self):
        program_text = """
using Turing

@model function model()
    i = 1
    while true
        U ~ Uniform(0., 1.)
        if U < 0.5
            break
        end
        i = i + 1
    end
    return i
end
        """
        variables = {"U": "U"}
        self._test_2(program_text, "julia", variables)

    def test_2_pyro(self):
        program_text = """
import pyro

def model():
    i = 1
    while True:
        U = pyro.sample("U", dist.Uniform(0.,1.))
        if U < 0.5:
            break
        i = i + 1
    return i
"""
        variables = {"U": "'U'"}
        self._test_2(program_text, "python", variables)

    def _test_3(self, program_text, language, variables):
        warnings = self._get_warnings(program_text, language)
        self.assertTrue(
            any(isinstance(warning, StochasticForLoopRangeWarning) for warning in warnings)
        )

    def test_3_turing(self):
        program_text = """
using Turing

@model function model()
    P ~ Poisson(3.)
    for i in 1:P
        U ~ Uniform(0., 1.)
    end
end
        """
        variables = {"P": "P", "U": "U"}
        self._test_3(program_text, "julia", variables)

    def test_3_pyro(self):
        program_text = """
import pyro

def model():
    P = pyro.sample("P", dist.Poisson(3.))
    for i in range(P):
        U = pyro.sample(f"U{i}", dist.Uniform(0.,1.))
"""
        variables = {"P": "'P'", "U": "'U'"}
        self._test_3(program_text, "python", variables)
        
    def _test_4(self, program_text, language, variables):
        warnings = self._get_warnings(program_text, language)
        self.assertTrue(
            any(isinstance(warning, SampleInRecursiveCallWarning) and warning.random_variable.name == variables["P"] for warning in warnings)
        )

    def test_4_turing(self):
        program_text = """
using Turing
# should use @submodel

function A()
    AA()
    return "A"
end
@model function P()
    P ~ Bernoulli(1.)
    return P
end
function AA()
    if P()
        return A()
    else
        return "AA"
    end
end
function B()
    return A()
end
function C()
    function D()
        return B()
    end
    function E()
        return D()
    end
    return E()
end
function F()
    return C()
end
@model function model()
    C()
end
"""
        variables = {"P": "P"}
        self._test_4(program_text, "julia", variables)

    def test_4_pyro(self):
        program_text = """
import pyro
def A():
    AA()
    return 'A'
def P():
    P = pyro.sample("P", dist.Bernoulli(1.))
    return P
def AA():
    if P():
        return A()
    else:
        return 'AA'

def B():
    return A()

def C():
    def D():
        return B()
    def E():
        return D()
    return E()

def F():
    return C()

def model():
    C()
"""
        variables = {"P": "'P'"}
        self._test_4(program_text, "python", variables)
        


if __name__ == "__main__":
    unittest.main()