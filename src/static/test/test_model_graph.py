
import unittest
import sys
sys.path.insert(0, 'src/static') # hack for now
from lasapp import ProbabilisticProgram

import os

from base_test_case import BaseTestCase
from analysis.model_graph import *

class TestModelGraph(BaseTestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)

    def _get_model_graph(self, program_text, language):
        path = self.write_program(program_text, language)
        program = ProbabilisticProgram(path)
        model_graph = get_model_graph(program)

        program.close()
        os.remove(path)

        # for _, x in model_graph.random_variables.items():
        #     print(x.name)
        # for x, y in model_graph.edges:
        #     print(x.name, "->", y.name)

        edges = [(x.name, y.name) for x, y in model_graph.edges]

        return model_graph, edges

    def _test_1(self, program_text, language, variables):
        model_graph, edges = self._get_model_graph(program_text, language)
        self.assertTrue(len(model_graph.random_variables) == 3)
        self.assertTrue(len(model_graph.edges) == 3)
        self.assertIn((variables["A"], variables["B"]), edges)
        self.assertIn((variables["A"], variables["C"]), edges)
        self.assertIn((variables["B"], variables["C"]), edges)

    def test_1_turing(self):
        program_text = """
using Turing

@model function model()
    A ~ Normal(0., 1.)
    B ~ Normal(A, 1.)
    C ~ Normal(A + B, 1.)
end
        """
        variables = {"A": "A", "B": "B", "C": "C"}
        self._test_1(program_text, "julia", variables)

    def test_1_pyro(self):
        program_text = """
import pyro

def model():
    A = pyro.sample("A", dist.Normal(0., 1.))
    B = pyro.sample("B", dist.Normal(A, 1.))
    C = pyro.sample("C", dist.Normal(A + B, 1.))
"""
        variables = {"A": "'A'", "B": "'B'", "C": "'C'"}
        self._test_1(program_text, "python", variables)

    def test_1_bm(self):
        program_text = """
import beanmachine.ppl as bm

@bm.random_variable
def A():
    return dist.Normal(0., 1.)

@bm.random_variable
def B():
    return dist.Normal(A(), 1.)

@bm.random_variable
def C():
    return dist.Normal(A() + B(), 1.)

# model = C
"""
        variables = {"A": "A()", "B": "B()", "C": "C()"}
        self._test_1(program_text, "python", variables)
        

    def _test_2(self, program_text, language, variables):
        model_graph, edges = self._get_model_graph(program_text, language)
        self.assertIn((variables["A"], variables["C"]), edges)
        self.assertIn((variables["B"], variables["C"]), edges)

    def test_2_turing(self):
        program_text = """
using Turing

@model function model()
    A ~ Bernoulli(0.5)
    B ~ Normal(0., 1.)
    if A
        C ~ Normal(B, 1.)
    else
        C ~ Normal(-B, 1.)
    end
end
        """
        variables = {"A": "A", "B": "B", "C": "C"}
        self._test_2(program_text, "julia", variables)

    def test_2_pyro(self):
        program_text = """
import pyro

def model():
    A = pyro.sample("A", dist.Bernoulli(0.5))
    B = pyro.sample("B", dist.Normal(0., 1.))
    if A:
        C = pyro.sample("C", dist.Normal(B, 1.))
    else:
        C = pyro.sample("C", dist.Normal(-B, 1.))
"""
        variables = {"A": "'A'", "B": "'B'", "C": "'C'"}
        self._test_2(program_text, "python", variables)

    def test_2_bm(self):
        program_text = """
import beanmachine.ppl as bm

@bm.random_variable
def A():
    return dist.Bernoulli(0.5)

@bm.random_variable
def B():
    return dist.Normal(0., 1.)

@bm.random_variable
def C():
    if A():
        return dist.Normal(B(), 1.)
    else:
        return dist.Normal(-B(), 1.)

# model = C
"""
        variables = {"A": "A()", "B": "B()", "C": "C()"}
        self._test_2(program_text, "python", variables)
            
    def _test_3(self, program_text, language, variables):
        model_graph, edges = self._get_model_graph(program_text, language)
        self.assertIn((variables["A"], variables["C"]), edges)
        self.assertIn((variables["B"], variables["C"]), edges)

    def test_3_turing(self):
        program_text = """
using Turing

@model function model()
    A ~ Bernoulli(0.5)
    B ~ Normal(0., 1.)
    if A
        mu = B
    else
        mu = -B
    end

    C ~ Normal(mu, 1.)
end
        """
        variables = {"A": "A", "B": "B", "C": "C"}
        self._test_3(program_text, "julia", variables)

    def test_3_pyro(self):
        program_text = """
import pyro

def model():
    A = pyro.sample("A", dist.Bernoulli(0.5))
    B = pyro.sample("B", dist.Normal(0., 1.))
    if A:
        mu = B
    else:
        mu = -B
        
    C = pyro.sample("C", dist.Normal(mu, 1.))
"""
        variables = {"A": "'A'", "B": "'B'", "C": "'C'"}
        self._test_3(program_text, "python", variables)

    def _test_4(self, program_text, language, variables):
        model_graph, edges = self._get_model_graph(program_text, language)
        self.assertIn((variables["A"], variables["B"]), edges)
        self.assertIn((variables["B"], variables["C"]), edges)

    def test_4_turing(self):
        program_text = """
using Turing

@model function submodel()
    A ~ Normal(0., 1.)
    B ~ Normal(A, 1.)
    return B
end

@model function model()
    B = @submodel submodel()
    C ~ Normal(B, 1.)
end
        """
        variables = {"A": "A", "B": "B", "C": "C"}
        self._test_4(program_text, "julia", variables) # TODO

    def test_4_pyro(self):
        program_text = """
import pyro

def submodel():
    A = pyro.sample("A", dist.Normal(0., 1.))
    B = pyro.sample("B", dist.Normal(A, 1.))
    return B

def model():
    B = submodel()
    C = pyro.sample("C", dist.Normal(B, 1.))
"""
        variables = {"A": "'A'", "B": "'B'", "C": "'C'"}
        self._test_4(program_text, "python", variables)


    def _test_5(self, program_text, language, variables):
        model_graph, edges = self._get_model_graph(program_text, language)
        self.assertIn((variables["A"], variables["B"]), edges)
        self.assertIn((variables["B"], variables["C"]), edges)

    def test_5_turing(self):
        program_text = """
using Turing

@model function submodel(A)
    B ~ Normal(A, 1.)
    return B
end

@model function model()
    A ~ Normal(0., 1.)
    B = @submodel submodel(A)
    C ~ Normal(B, 1.)
end
        """
        variables = {"A": "A", "B": "B", "C": "C"}
        # self._test_5(program_text, "julia", variables) # TODO?

    def test_5_pyro(self):
        program_text = """
import pyro

def submodel(A):
    B = pyro.sample("B", dist.Normal(A, 1.))
    return B

def model():
    A = pyro.sample("A", dist.Normal(0., 1.))
    B = submodel(A)
    C = pyro.sample("C", dist.Normal(B, 1.))
"""
        variables = {"A": "'A'", "B": "'B'", "C": "'C'"}
        # self._test_5(program_text, "python", variables) # TODO?

if __name__ == "__main__":
    unittest.main()