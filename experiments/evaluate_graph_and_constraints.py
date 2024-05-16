import sys
sys.path.insert(0, 'src/static')
import argparse

from lasapp import ProbabilisticProgram, infer_distribution_properties

from analysis.model_graph import *
from analysis.constraint_verification import *
from analysis.hmc_assumptions_checker import *
from analysis.guide_validation import *
from analysis.utils import *

from eval_utils import *
import time
            
def get_gt_graph_from_comments(filename):
    file_content = get_file_content(filename)

    _, _, model_graph_str = file_content.partition("# MODELGRAPH:\n")
    model_graph_str, _, _ = model_graph_str.partition("\n# END_MODELGRAPH")
    model_graph_line_str = model_graph_str.splitlines()
    assert model_graph_line_str[0] == "# nodes:"
    assert model_graph_line_str[2] == "# edges:"
    if "-" in model_graph_line_str[1]:
        # useful if , is in rv name
        gt_nodes = model_graph_line_str[1].lstrip("# ").split(" - ")
    else:
        gt_nodes = model_graph_line_str[1].lstrip("# ").split(", ")
    gt_edges = [tuple(edge_line_str.lstrip("# ").split(" -> ", maxsplit=2)) for edge_line_str in model_graph_line_str[3:]]

    return set(gt_nodes), set(gt_edges)

def check_model_graph(filename, n_unroll_loops=0, plot=False):
   
    try:
        program = ProbabilisticProgram(filename, n_unroll_loops=n_unroll_loops)
        model = program.get_model()
        print("Model:", model.name)
        model_graph = get_model_graph(program)
        if plot:
            plot_model_graph(model_graph, label_method="name")
    except Exception as e:
        print(e)
        return False
            
    nodes = set([rv.address_node.source_text for (_, rv) in model_graph.random_variables.items()])
    edges = set([(rv1.address_node.source_text, rv2.address_node.source_text) for (rv1, rv2) in model_graph.edges])
    # NOTE: the model graph is given in terms of sourcetext of the address node,
    # which is different to the random variable name when loop unrolling is applied
    gt_nodes, gt_edges = get_gt_graph_from_comments(filename)

    check = (gt_nodes == nodes) and (gt_edges == edges)

    if check:
        pass
    else:
        if nodes != gt_nodes:
            nodes_missing = gt_nodes.difference(nodes)
            if len(nodes_missing) > 0:
                print("Nodes missing:")
                print(nodes_missing)
            wrong_nodes = nodes.difference(gt_nodes)
            if len(wrong_nodes) > 0:
                print("Wrong nodes:")
                print(wrong_nodes)
        if edges != gt_edges:
            missing_edges = gt_edges.difference(edges)
            if len(missing_edges) > 0:
                print("Edges missing:")
                print(missing_edges)
            wrong_edges = edges.difference(gt_edges)
            if len(wrong_edges) > 0:
                print("Wrong edges:")
                print(wrong_edges)

    return check

def check_distributions(filename):
    try:
        program = ProbabilisticProgram(filename)
        rvs = program.get_random_variables()
        is_ok = True
        for rv in rvs:
            if infer_distribution_properties(rv) is None:
                is_ok = False
                print(rv.distribution.name, rv.distribution.node.source_text)
        return is_ok
    except Exception as e:
        print(e)
        return False
    

def check_verify_distribution_constraints(filename):
    try:
        program = ProbabilisticProgram(filename)
        violations = validate_distribution_arg_constraints(program)
        if len(violations) > 0:
            for violation in violations:
                print(violation)
            return False
        else:
            return True
    except Exception as e:
        print(e)
        
        return False

import os
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-ppl", help="pymc | turing | both", default="both", required=False)
    parser.add_argument("-analysis", help="graph | constraint | both", default="both", required=False)
    args = parser.parse_args()

    n_unroll_loops = 3

    # filename = "evaluation/turing/turing_tutorials/04-hidden-markov-model.jl"
    # check = check_model_graph(filename, plot=True, n_unroll_loops=n_unroll_loops)
    # check_distributions(filename)
    # check = check_verify_distribution_constraints(filename)
    # if check:
    #     print("Is ok :)")
    # exit(1)

    turing_folders = [
        "evaluation/turing/statistical_rethinking_2/", "evaluation/turing/turing_tutorials/"
    ]
    pymc_folders = [
        "evaluation/pymc/Bayes_Rules", "evaluation/pymc/BDA3",  "evaluation/pymc/BCM/ParameterEstimation", "evaluation/pymc/BCM/ModelSelection", "evaluation/pymc/BCM/CaseStudies"
    ]
    if args.ppl == "pymc":
        folders = pymc_folders
    elif args.ppl == "turing":
        folders = turing_folders
    else:
        folders = pymc_folders + turing_folders
        # model graph : 8/214
        # constraint violations: 69/214
        # 10.3 seconds

    do_graph = args.analysis in ("graph", "both")
    do_constraint = args.analysis in ("constraint", "both")


    filenames = []
    for folder in folders:
        for entry in os.scandir(folder):
            if entry.is_file() and (entry.name.endswith(".jl") or entry.name.endswith(".py")):
                filenames.append(entry.path)
    filenames = sorted(filenames)


    t0 = time.time()
    error_count_model = 0
    error_count_constraint = 0
    for filename in filenames:
        print(bcolors.HEADER + "## " + filename + bcolors.ENDC)
        check_model = check_model_graph(filename, n_unroll_loops=n_unroll_loops) if do_graph else True
        check_constraint = check_verify_distribution_constraints(filename) if do_constraint else True
        error_count_model += (1 - check_model)
        error_count_constraint += (1 - check_constraint)
        if not check_model or not check_constraint:
            print_notes(filename)
            print(bcolors.FAIL + "Warnings produced" + bcolors.ENDC)
        else:
            print(bcolors.OKGREEN + "Everything is ok" + bcolors.ENDC)
        print()

    t1 = time.time()
    print()
    if do_graph:
        print(f"Model Graph   Error Count: {error_count_model}/{len(filenames)}")
        # print(f"Model Graph Correct Count: {len(filenames)-error_count_model}/{len(filenames)}")
    if do_constraint:
        print(f"Constraint    Error Count: {error_count_constraint}/{len(filenames)}")
        # print(f"Constraint  Correct Count: {len(filenames)-error_count_constraint}/{len(filenames)}")
    print(f"in {t1-t0:.2f} seconds.")