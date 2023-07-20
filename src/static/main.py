
from lasapp import ProbabilisticProgram

from analysis.model_graph import *
from analysis.constraint_verfication import *
from analysis.hmc_assumptions_checker import *
from analysis.guide_validation import *
from analysis.utils import *

def main(file):
    program = ProbabilisticProgram(file)

    model = program.get_model()
    print("Model:", model.name)

    # response = program.client.get_random_variables(
    #         file_name=program.file_name, ppl=program.ppl
    #     )
    # print(response)
    # program.close()
    # exit()

    file_content = get_file_content(file)
    variables = program.get_random_variables()
    highlights = [(rv.node.first_byte, rv.node.last_byte, "106m" if rv.is_observed else "102m") for rv in variables]
    print_source_highlighted(file_content, highlights)

    # model_graph = get_model_graph(program)
    # plot_model_graph(model_graph, merge_by_name=True)

    # violations = validate_distribution_arg_constraints(program)
    # print_source_highlight_violations(violations)

    # warnings = check_hmc_assumptions(program)
    # if len(warnings) == 0:
    #     print("No HMC warnings.")
    # for (i, warning) in enumerate(warnings):
    #     print(f"{i+1:2d}: {warning}")
    
    violations = check_guide(program)
    for (i, v) in enumerate(violations):
        print(f"{i+1}.:", v)

    program.close()

if __name__ == '__main__':
    # file = "tmp_test_file.py"

    # file = "test/linear_regression/linreg_pyro.py"
    # file = "test/pedestrian/pedestrian_pyro.py"
    # file = "test/test/submodel_pyro.py"
    # file = "test/test/pedestrian_pyro.py"
    # file = "test/test/guide_pyro.py"


    # file = "test/linear_regression/linreg_pymc.py"
    # file = "test/test/constraints_pymc.py"
    
    # file = "test/linear_regression/linreg_beanmachine.py"

    # file = "test/linear_regression/linreg_turing.jl"
    # file = "test/gmm/gmm_turing_2.jl"
    # file = "test/hmm/hmm_turing.jl"
    # file = "test/burglary/burglary_turing.jl"
    # file = "test/test/slicing_turing.jl"
    file = "test/test/guide_gen.jl"

    # file = "test/linear_regression/linreg_gen.jl"
    # file = "test/test/constraints_gen.jl"

    main(file)
