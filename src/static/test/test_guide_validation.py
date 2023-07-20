
import unittest
import sys
sys.path.insert(0, 'src/static') # hack for now
from lasapp import ProbabilisticProgram

import os

from base_test_case import BaseTestCase
from analysis.guide_validation import *

class TestGuideValidation(BaseTestCase):
    def _get_violations(self, program_text, language):
        path = self.write_program(program_text, language)
        program = ProbabilisticProgram(path)
        violations = check_guide(program)
        program.close()
        os.remove(path)
        return violations
    
    def _test_1(self, program_text, language, variables):
        violations = self._get_violations(program_text, language)
        self.assertTrue(any(isinstance(v, OverlappingSampleStatements) and v.rv_name == variables["D"] for v in violations))
        self.assertTrue(any(isinstance(v, SupportIntervalMismatch) and v.rv_name == variables["B"] for v in violations))
        self.assertTrue(
            sum(1 for v in violations
                if isinstance(v, AbsoluteContinuityViolation) and 
                v.rv_name in (variables["B"], variables["D"], variables["E"])) == 3
                )
        
        # for (i, v) in enumerate(violations):
        #     print(f"{i+1}.:", v)

    
    def test_1_pyro(self):
        program_text = """
import pyro
import pyro.distributions as dist

def model(I: bool):
    A = pyro.sample('A', dist.Bernoulli(0.5))

    if A == 1:
        B = pyro.sample('B', dist.Normal(0., 1.))
    else:
        B = pyro.sample('B', dist.Gamma(1, 1))

    if B > 1 and I:
        pyro.sample('C', dist.Beta(1, 1))
    if B < 1 and I:
        pyro.sample('D', dist.Normal(0., 1.))
    if B < 2:
        pyro.sample('D', dist.Normal(0., 2.)) # Duplicated
        pyro.sample('E', dist.Normal(0., 1.))


def guide(I: bool):
    if I:
        A = pyro.sample('A', dist.Bernoulli(0.9))
    else:
        A = pyro.sample('A', dist.Bernoulli(0.1))

    B = pyro.sample('B', dist.Gamma(1, 1)) # Wrong Support

    if B > 1 and I:
        pyro.sample('C', dist.Uniform(0, 1))
    else:
        pyro.sample('D', dist.Normal(0., 1.))
        pyro.sample('E', dist.Normal(0., 1.)) # Not for 1 < B < 2 and I

"""

        self._test_1(program_text, "python", {"A": "'A'", "B": "'B'", "C": "'C'", "D": "'D'", "E": "'E'"})

    def test_1_gen(self):
        program_text = """
using Gen

@gen function model(I:: Bool)
    A  ~ bernoulli(0.5)

    if A == 1
        B ~ normal(0., 1.)
    else
        B ~ gamma(1, 1)
    end

    if B > 1 && I
        {:C} ~ beta(1, 1)
    end
    if B < 1 && I
        {:D} ~ normal(0., 1.)
    end
    if B < 2
        {:D} ~ normal(0., 2.) # Duplicated
        {:E} ~ normal(0., 1.)
    end
end

@gen function guide(I:: Bool)
    if I
        A ~ bernoulli(0.9)
    else
        A ~ bernoulli(0.1)
    end

    B ~ gamma(1, 1) # Wrong Support

    if B > 1 && I
        {:C} ~ uniform_continuous(0, 1)
    else
        {:D} ~ normal(0., 1.)
        {:E} ~ normal(0., 1.) # Not for 1 < B < 2 and I
    end
end

        """
        self._test_1(program_text, "julia", {"A": "A", "B": "B", "C": "C", "D": "D", "E": "E"})

if __name__ == "__main__":
    unittest.main()