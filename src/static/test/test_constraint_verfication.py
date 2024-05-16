
import unittest
import sys
sys.path.insert(0, 'src/static') # hack for now
from lasapp import ProbabilisticProgram

import os

from base_test_case import BaseTestCase
from analysis.constraint_verification import *

class TestConstraintVerification(BaseTestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)

    def _get_violations(self, program_text, language):
        path = self.write_program(program_text, language)
        program = ProbabilisticProgram(path)
        violations = validate_distribution_arg_constraints(program)
        program.close()
        os.remove(path)
        return violations

    def _test_1(self, program_text, language, variables):
        violations = self._get_violations(program_text, language)
        rvs = [v.random_variable.name for v in violations]

        self.assertIn(variables["B1"], rvs)
        self.assertNotIn(variables["B2"], rvs)

    def test_1_turing(self):
        program_text = """
using Turing

@model function model()
    p ~ Normal(0., 1.)
    B1 ~ Bernoulli(p)
    B2 ~ Bernoulli(1/(1 + exp(p)))
end
        """
        variables = {"p": "p", "B1": "B1", "B2": "B2"}
        self._test_1(program_text, "julia", variables)

    def test_1_pyro(self):
        program_text = """
import pyro

def model():
    p = pyro.sample("p", dist.Normal(0., 1.))
    B1 = pyro.sample("B1", dist.Bernoulli(p))
    B2 = pyro.sample("B2", dist.Bernoulli(1/(1 + p.exp())))
"""
        variables = {"p": "'p'", "B1": "'B1'", "B2": "'B2'"}
        self._test_1(program_text, "python", variables)

    def test_1_bm(self):
        program_text = """
import beanmachine.ppl as bm

@bm.random_variable
def p():
    return dist.Normal(0., 1.)

@bm.random_variable
def B1():
    return dist.Bernoulli(p())

@bm.random_variable
def B2():
    return dist.Bernoulli(1/(1 + p().exp()))

# model = B2
"""
        variables = {"p": "p()", "B1": "B1()", "B2": "B2()"}
        self._test_1(program_text, "python", variables)
        
    def _test_2(self, program_text, language, variables):
        violations = self._get_violations(program_text, language)
        rvs = [v.random_variable.name for v in violations]

        self.assertIn(variables["C"], rvs)
        self.assertIn(variables["E"], rvs)
        self.assertNotIn(variables["A"], rvs)
        self.assertNotIn(variables["B"], rvs)
        self.assertNotIn(variables["D"], rvs)
    
    def test_2_turing(self):
        program_text = """
using Turing

@model function model()
    A ~ Normal(0., 1.)
    B ~ Gamma(2., 2.)
    C ~ Bernoulli(2.)

    if C
        s1 = A^2
        s2 = A
    else
        s1 = B
        s2 = s1
    end

    D ~ Normal(0., s1)
    E ~ Normal(0., s2)
end
        """
        variables = {"A": "A", "B": "B", "C": "C", "D": "D", "E": "E"}
        self._test_2(program_text, "julia", variables)

    def test_2_pyro(self):
        program_text = """
import pyro

def model():
    A = pyro.sample("A", dist.Normal(0., 1.))
    B = pyro.sample("B", dist.Gamma(2., 2.))
    C = pyro.sample("C", dist.Bernoulli(2.))

    if C:
        s1 = A**2
        s2 = A
    else:
        s1 = B
        s2 = s1

    D = pyro.sample("D", dist.Normal(0., s1))
    E = pyro.sample("E", dist.Normal(0., s2))
    
    
"""
        variables = {"A": "'A'", "B": "'B'", "C": "'C'", "D": "'D'", "E": "'E'"}
        self._test_2(program_text, "python", variables)

    def test_2_bm(self):
        program_text = """
import beanmachine.ppl as bm

@bm.random_variable
def A():
    return dist.Normal(0., 1.)

@bm.random_variable
def B():
    return dist.Gamma(2., 2.)

@bm.random_variable
def C():
    return dist.Bernoulli(2.)

@bm.random_variable
def D():
    if C():
        s1 = A()**2
    else:
        s2 = B()
    return dist.Normal(0., s1)

@bm.random_variable
def E():
    if C():
        s2 = A()
    else:
        s2 = B()
    return dist.Normal(0., s2)

# model = E
"""
        variables = {"A": "A()", "B": "B()", "C": "C()", "D": "D()", "E": "E()"}
        self._test_2(program_text, "python", variables)
    

if __name__ == "__main__":
    unittest.main()

