import sys
sys.path.insert(0, 'src/static')

from lasapp import ProbabilisticProgram

from analysis.model_graph import *
from analysis.guide_validation import *
from analysis.utils import *

from eval_utils import *
import time
import os

def check_program(filename: str, n_unroll_loops=0, plot=False):
    try:
        program = ProbabilisticProgram(filename, n_unroll_loops)

        if plot:
            model_graph = get_model_graph(program)
            plot_model_graph(model_graph, filename="model")

            guide_graph = get_guide_graph(program)
            plot_model_graph(guide_graph, filename="guide")
        
        check = True

        print(bcolors.BOLD + "Check Proposal (model << guide)" + bcolors.ENDC)
        violations = check_proposal(program)
        for (i, v) in enumerate(violations):
            print(f"{i+1}.:", v)

        check = check and len(violations) == 0

        print(bcolors.BOLD + "Check SVI (guide << model)" + bcolors.ENDC)
        violations = check_svi(program)
        for (i, v) in enumerate(violations):
            print(f"{i+1}.:", v)

        check = check and len(violations) == 0

        return check
        
    except Exception as e:
        print(e)
        return False
    


if __name__ == "__main__":
    n_unroll_loops = 3

    # filename = "evaluation/pyro/air.py"
    # check_program(filename, n_unroll_loops=n_unroll_loops, plot=True)
    # exit(0)

    folder = "evaluation/pyro"

    filenames = []
    for entry in os.scandir(folder):
        if entry.is_file() and (entry.name.endswith(".jl") or entry.name.endswith(".py")):
            filenames.append(entry.path)
    filenames = sorted(filenames)

    t0 = time.time()
    warning_count = 0
    for filename in filenames:
        print(bcolors.HEADER + "## " + filename + bcolors.ENDC)
        check = check_program(filename, n_unroll_loops=n_unroll_loops)
        warning_count += (1 - check)
        if not check:
            print_notes(filename)
            print(bcolors.FAIL + "Warnings produced" + bcolors.ENDC)
        else:
            print(bcolors.OKGREEN + "Everything is ok" + bcolors.ENDC)
        print()
    t1 = time.time()

    print(f"{warning_count} / {len(filenames)} warnings.")
    print(f"in {t1-t0:.2f} seconds.")
    # 2 / 8 warnings.
    # 1.24 seconds