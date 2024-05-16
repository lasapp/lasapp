import sys
sys.path.insert(0, 'src/static')

from lasapp import ProbabilisticProgram, infer_distribution_properties

from analysis.model_graph import *
from analysis.hmc_assumptions_checker import *
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
        
        warnings = check_hmc_assumptions(program)
        if len(warnings) == 0:
            print("No HMC warnings.")
        for (i, warning) in enumerate(warnings):
            print(f"{i+1:2d}: {warning}\n")

        return len(warnings) == 0
        
    except Exception as e:
        print(e)
        return False
    


if __name__ == "__main__":
    n_unroll_loops = 0

    # filename = "evaluation/gen/binary_classify.jl"
    # check_program(filename, n_unroll_loops=n_unroll_loops, plot=True)
    # exit(0)

    folder = "evaluation/gen"

    
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
            print(bcolors.FAIL + "Warnings produced" + bcolors.ENDC)
        else:
            print_notes(filename)
            print(bcolors.OKGREEN + "Everything is ok" + bcolors.ENDC)
        print()
    t1 = time.time()

    print(f"{warning_count} / {len(filenames)} warnings.")
    print(f"in {t1-t0:.2f} seconds.")
    # 7 / 8 warnings.
    # 0.25 seconds