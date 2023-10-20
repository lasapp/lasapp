import sys
sys.path.insert(0, 'src/static')
import argparse

import lasapp
from analysis.model_graph import *
from analysis.constraint_verfication import *
from analysis.hmc_assumptions_checker import *
from analysis.guide_validation import *
from analysis.utils import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("program_name", help="motivating | linear_model | slicing | pedestrian | constraint | guide")
    parser.add_argument("ppl", help="turing | gen | pyro | pymc | beanmachine")
    parser.add_argument("-a", help="graph | hmc | constraint | guide", default="paper") 
    parser.add_argument("-v", help="if set source code of file will be printed", action='store_true')
    args = parser.parse_args()

    ext = {"turing": "jl", "gen": "jl", "pyro": "py", "pymc": "py", "beanmachine": "py"}[args.ppl]
    filename = f"experiments/examples/{args.program_name}_{args.ppl}.{ext}"

    program = lasapp.ProbabilisticProgram(filename)

    if args.v:
        file_content = get_file_content(filename)
        variables = program.get_random_variables()
        highlights = [(rv.node.first_byte, rv.node.last_byte, "106m" if rv.is_observed else "102m") for rv in variables]
        print_source_highlighted(file_content, highlights)
    # print()
    # print("RVs:")
    # for rv in variables:
    #     print(rv.name, rv.distribution.node.source_text)

    if args.a == "paper":
        analysis = {
            "motivating": "hmc",
            "pedestrian": "hmc",
            "slicing": "graph",
            "linear_model": "constraint",
            "constraint": "constraint",
            "guide": "guide"
        }[args.program_name]
    else:
        analysis = args.a

    if analysis == "hmc":
        warnings = check_hmc_assumptions(program)
        if len(warnings) == 0:
            print("No HMC warnings.")
        for (i, warning) in enumerate(warnings):
            print(f"{i+1:2d}: {warning}")

    elif analysis == "graph":
        model_graph = get_model_graph(program)
        print("Model Graph Edges:")
        merge_nodes_by_name(model_graph)
        for x,y in model_graph.edges:
            print(x.name, "->", y.name)
        plot_model_graph(model_graph, view=False)

    elif analysis == "constraint":
        violations = validate_distribution_arg_constraints(program)
        print_source_highlight_violations(violations)

    elif analysis == "guide":
        assert args.program_name == "guide"
        violations = check_guide(program)
        if len(violations) == 0:
            print("No warnings.")
        for (i, v) in enumerate(violations):
            print(f"{i+1}.:", v)


