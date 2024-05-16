import sys
sys.path.insert(0, 'src/static')
import argparse

import lasapp
from analysis.model_graph import *
from analysis.constraint_verification import *
from analysis.hmc_assumptions_checker import *
from analysis.guide_validation import *
from analysis.utils import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="path to probabilistic program")
    parser.add_argument("-a", help="graph | hmc | constraint | guide-proposal | guide-svi", default="graph") 
    parser.add_argument("-v", help="if set source code of file will be printed", action='store_true')
    args = parser.parse_args()

    filename = args.filename

    program = lasapp.ProbabilisticProgram(filename, n_unroll_loops=3)

    if args.v:
        file_content = get_file_content(filename)
        variables = program.get_random_variables()
        highlights = [(rv.node.first_byte, rv.node.last_byte, "106m" if rv.is_observed else "102m") for rv in variables]
        print_source_highlighted(file_content, highlights)
    # print()
    # print("RVs:")
    # for rv in variables:
    #     print(rv.name, rv.distribution.node.source_text)

    analysis = args.a

    if analysis == "hmc":
        warnings = check_hmc_assumptions(program)
        if len(warnings) == 0:
            print("No HMC warnings.")
        warnings = set(map(str, warnings))
        for (i, warning) in enumerate(warnings):
            print(f"{i+1:2d}: {warning}")

    elif analysis == "graph":
        model_graph = get_model_graph(program)
        print("Model Graph Edges:")
        merge_nodes_by_name(model_graph)
        for x,y in model_graph.edges:
            print(x.name, "->", y.name)
        plot_model_graph(model_graph, view=True)

    elif analysis == "constraint":
        violations = validate_distribution_arg_constraints(program)
        print_source_highlight_violations(violations)

    elif analysis == "guide-proposal":
        violations = check_proposal(program)
        if len(violations) == 0:
            print("No warnings.")
        for (i, v) in enumerate(violations):
            print(f"{i+1}.:", v)

    elif analysis == "guide-svi":
        violations = check_svi(program)
        if len(violations) == 0:
            print("No warnings.")
        for (i, v) in enumerate(violations):
            print(f"{i+1}.:", v)

