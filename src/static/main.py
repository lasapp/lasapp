
from lasapp import ProbabilisticProgram

from analysis.model_graph import *
from analysis.constraint_verification import *
from analysis.hmc_assumptions_checker import *
from analysis.guide_validation import *
from analysis.utils import *

def main(file):
    program = ProbabilisticProgram(file, n_unroll_loops=3)

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

    model_graph = get_model_graph(program)
    # merge_nodes_by_name(model_graph)
    plot_model_graph(model_graph, filename="model")

    # guide_graph = get_guide_graph(program)
    # # merge_nodes_by_name(model_graph)
    # plot_model_graph(guide_graph, filename="guide")

    # violations = validate_distribution_arg_constraints(program)
    # print_source_highlight_violations(violations)

    warnings = check_hmc_assumptions(program)
    if len(warnings) == 0:
        print("No HMC warnings.")
    for (i, warning) in enumerate(warnings):
        print(f"{i+1:2d}: {warning}")
    
    # print("Check Guide")
    # violations = check_guide(program)
    # for (i, v) in enumerate(violations):
    #     print(f"{i+1}.:", v)

    # print("Check SVI")
    # violations = check_svi(program)
    # for (i, v) in enumerate(violations):
    #     print(f"{i+1}.:", v)

    program.close()

if __name__ == '__main__':
    # file = "tmp_test_file.py"

    # file = "examples/linear_regression/linreg_pyro.py"
    # file = "examples/pedestrian/pedestrian_pyro.py"
    # file = "examples/test/submodel_pyro.py"
    # file = "examples/test/pedestrian_pyro.py"
    # file = "examples/test/guide_pyro.py"
    # file = "examples/test/guide_pyro_2.py"
    # file = "examples/test/lazy_if.py"
    # file = "examples/test/hurricane.py"
    # file = "examples/test/func_deps.jl"
    # file = "examples/test/loop_deps.jl"
    # file = "examples/test/pymc_preproc.py"

    # file = "evaluation/pyro/dmm.py"
    # file = "evaluation/gen/heavytail_piecewise.jl"
    # file = "evaluation/gen/pedestrian.jl"
    # file = "evaluation/gen/simple.jl"
    # file = "evaluation/gen/stochastic_support.jl"
    file = "evaluation/gen/capture_recapture.jl"

    # file = "examples/linear_regression/linreg_pymc.py"
    # file = "examples/test/constraints_pymc.py"
    
    # file = "examples/linear_regression/linreg_beanmachine.py"

    # file = "examples/linear_regression/linreg_turing.jl"
    # file = "examples/gmm/gmm_turing_2.jl"
    # file = "examples/hmm/hmm_turing.jl"
    # file = "examples/burglary/burglary_turing.jl"
    # file = "examples/test/slicing_turing.jl"
    # file = "examples/test/guide_gen.jl"

    # file = "examples/linear_regression/linreg_gen.jl"
    # file = "examples/test/constraints_gen.jl"


    # file = "examples/gmm/gmm_turing.jl"
    # file = "examples/gmm/gmm_turing_2.jl"
    # file = "examples/gmm/gmm_turing_3.jl"
    main(file)
