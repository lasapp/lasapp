import sys
sys.path.insert(0, 'src/static')
import unittest
import lasapp
from analysis.model_graph import *
from analysis.constraint_verfication import *
from analysis.hmc_assumptions_checker import *
from analysis.guide_validation import *
from analysis.utils import *

class ICSE24(unittest.TestCase):
    def _test_motivating(self, filename, ppl, variables):
        program = lasapp.ProbabilisticProgram(filename)
        warnings = check_hmc_assumptions(program)
        # print()
        # print(ppl)
        # for rv in program.get_random_variables():
        #     print(rv.name)

        program.close()

        self.assertTrue(
            any(isinstance(warning, ContinuousDistributionViolation) and warning.random_variable.name == variables["state"] for warning in warnings)
        )
        if ppl != "pymc":
            self.assertTrue(
                any(isinstance(warning, RandomControlDependentWarning) and warning.random_variable.name == variables["x"] for warning in warnings)
            )
        
    def test_motivating_beanmachine(self):
        self._test_motivating("icse24/examples/motivating_beanmachine.py", "beanmachine", {"state": "state()", "x": "model(n)"})

    def test_motivating_gen(self):
        self._test_motivating("icse24/examples/motivating_gen.jl", "gen", {"state": "state", "x": ":x => i"})

    def test_motivating_pymc(self):
        self._test_motivating("icse24/examples/motivating_pymc.py", "pymc", {"state": "'state'", "x": "'X'"})

    def test_motivating_pyro(self):
        self._test_motivating("icse24/examples/motivating_pyro.py", "pyro", {"state": "'state'", "x": "'X'"})

    def test_motivating_turing(self):
        self._test_motivating("icse24/examples/motivating_turing.jl", "turing", {"state": "state", "x": "X[i]"})


    def _test_constraint(self, filename, ppl, variables):
        program = lasapp.ProbabilisticProgram(filename)
        violations = validate_distribution_arg_constraints(program)
        # print()
        # print(ppl)
        # for rv in program.get_random_variables():
        #     print(rv.name)

        program.close()

        rvs = [v.random_variable.name for v in violations]

        self.assertIn(variables["g"], rvs)
        
    def test_constraint_beanmachine(self):
        self._test_constraint("icse24/examples/constraint_beanmachine.py", "beanmachine", {"g": "g()"})

    def test_constraint_gen(self):
        self._test_constraint("icse24/examples/constraint_gen.jl", "gen", {"g": "g"})

    def test_constraint_pymc(self):
        self._test_constraint("icse24/examples/constraint_pymc.py", "pymc", {"g": "'g'"})

    def test_constraint_pyro(self):
        self._test_constraint("icse24/examples/constraint_pyro.py", "pyro", {"g": "'g'"})

    def test_constraint_turing(self):
        self._test_constraint("icse24/examples/constraint_turing.jl", "turing", {"g": "g"})


    def _test_guide(self, filename, ppl, variables):
        program = lasapp.ProbabilisticProgram(filename)
        violations = check_guide(program)
        # print()
        # print(ppl)
        # for rv in program.get_random_variables():
        #     print(rv.name)

        program.close()

        self.assertTrue(any(isinstance(v, OverlappingSampleStatements) and v.rv_name == variables["D"] for v in violations))
        self.assertTrue(any(isinstance(v, SupportIntervalMismatch) and v.rv_name == variables["B"] for v in violations))
        self.assertTrue(
            sum(1 for v in violations
                if isinstance(v, AbsoluteContinuityViolation) and 
                v.rv_name in (variables["B"], variables["D"], variables["E"])) == 3
                )

    def test_guide_gen(self):
        self._test_guide("icse24/examples/guide_gen.jl", "gen", {"B": "B", "D": "D", "E": "E"})

    def test_guide_pyro(self):
        self._test_guide("icse24/examples/guide_pyro.py", "pyro", {"B": "'B'", "D": "'D'", "E": "'E'"})



    def _test_linear(self, filename, ppl, variables):
        program = lasapp.ProbabilisticProgram(filename)
        violations = validate_distribution_arg_constraints(program)
        # print()
        # print(ppl)
        # for rv in program.get_random_variables():
        #     print(rv.name)

        program.close()

        rvs = [v.random_variable.name for v in violations]

        self.assertIn(variables["sigma"], rvs)


    def test_linear_beanmachine(self):
        self._test_linear("icse24/examples/linear_model_beanmachine.py", "beanmachine", {"sigma": "linear_regression_2(x)"})

    def test_linear_gen(self):
        self._test_linear("icse24/examples/linear_model_gen.jl", "gen", {"sigma": ":y=>i"})

    def test_linear_pymc(self):
        self._test_linear("icse24/examples/linear_model_pymc.py", "pymc", {"sigma": "'y'"})

    def test_linear_pyro(self):
        self._test_linear("icse24/examples/linear_model_pyro.py", "pyro", {"sigma": "'y'"})

    def test_linear_turing(self):
        self._test_linear("icse24/examples/linear_model_turing.jl", "turing", {"sigma": "y[i]"})


    def _test_pedestrian(self, filename, ppl, variables):
        program = lasapp.ProbabilisticProgram(filename)
        warnings = check_hmc_assumptions(program)
        # print()
        # print(ppl)
        # for rv in program.get_random_variables():
        #     print(rv.name)

        program.close()

        self.assertTrue(
            any(isinstance(warning, DefinitionInWhileLoopWarning) and warning.random_variable.name == variables["step"] for warning in warnings)
        )


        self.assertTrue(
            any(isinstance(warning, RandomControlDependentWarning) and warning.random_variable.name == variables["obs"] for warning in warnings)
        )

        self.assertTrue(
            any(isinstance(warning, RandomControlDependentWarning) and warning.random_variable.name == variables["step"] and len(warning.random_control_deps) == 2 for warning in warnings)
        )

    def test_pedestrian_beanmachine(self):
        program = lasapp.ProbabilisticProgram("icse24/examples/pedestrian_beanmachine.py")
        warnings = check_hmc_assumptions(program)
        program.close()

        self.assertTrue(
            any(isinstance(warning, SampleInRecursiveCallWarning) and warning.random_variable.name == "position(t)" for warning in warnings)
        )
        self.assertTrue(
            any(isinstance(warning, RandomControlDependentWarning) and warning.random_variable.name == "end_distance()" for warning in warnings)
        )


    def test_pedestrian_gen(self):
        self._test_pedestrian("icse24/examples/pedestrian_gen.jl", "gen", {"start": "start", "step": ":step=>t", "obs": "end_distance"})

    def test_pedestrian_pyro(self):
        self._test_pedestrian("icse24/examples/pedestrian_pyro.py", "pyro", {"start": "'start'", "step": "f'step_{t}'", "obs": "'obs'"})

    def test_pedestrian_turing(self):
        self._test_pedestrian("icse24/examples/pedestrian_turing.jl", "turing", {"start": "start", "step": "step[t]", "obs": "end_distance"})



    def _test_slicing(self, filename, ppl, variables):
        program = lasapp.ProbabilisticProgram(filename)

        model_graph = get_model_graph(program)

        program.close()

        for _, x in model_graph.random_variables.items():
            self.assertEqual(x.is_observed, variables["g"] == x.name)
            

        edges = [(x.name, y.name) for x, y in model_graph.edges]


        self.assertIn((variables["i"], variables["s"]), edges)
        self.assertIn((variables["i"], variables["g"]), edges)
        self.assertIn((variables["d"], variables["g"]), edges)
        self.assertIn((variables["g"], variables["l"]), edges)


    def test_slicing_beanmachine(self):
        self._test_slicing("icse24/examples/slicing_beanmachine.py", "beanmachine", {"i": "i()", "s": "s()", "d": "d()", "g": "g()", "l": "l()"})

    def test_slicing_gen(self):
        self._test_slicing("icse24/examples/slicing_gen.jl", "gen", {"i": "i", "s": "s", "d": "d", "g": "g", "l": "l"})

    def test_slicing_pymc(self):
        self._test_slicing("icse24/examples/slicing_pymc.py", "pymc", {"i": "'i'", "s": "'s'", "d": "'d'", "g": "'g'", "l": "'l'"})

    def test_slicing_pyro(self):
        self._test_slicing("icse24/examples/slicing_pyro.py", "pyro", {"i": "'i'", "s": "'s'", "d": "'d'", "g": "'g'", "l": "'l'"})

    def test_slicing_turing(self):
        self._test_slicing("icse24/examples/slicing_turing.jl", "turing", {"i": "i", "s": "s", "d": "d", "g": "g", "l": "l"})

if __name__ == "__main__":
    unittest.main()

