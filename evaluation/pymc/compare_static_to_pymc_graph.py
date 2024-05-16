import os
import subprocess

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def get_gt_graph_from_comments(file_content):

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


command = """
graph = pm.model_to_graphviz(model)
print(graph)
"""
import re
def strip_apostrophe(x):
    return x.lstrip("'").rstrip("'")


# folder = "evaluation/pymc/Bayes_Rules"
# folder = "evaluation/pymc/BDA3"
# folder = "evaluation/pymc/BCM/ModelSelection"
# folder = "evaluation/pymc/BCM/ParameterEstimation"
folder = "evaluation/pymc/BCM/CaseStudies"
tmp_file = folder + "/tmp.py"

filenames = []
for entry in os.scandir(folder):
    if entry.is_file() and (entry.name.endswith(".jl") or entry.name.endswith(".py")):
        filenames.append((entry.path, entry.name))
filenames = sorted(filenames)

# i = 26
# filenames = filenames[i:i+1]

for i, (path, name) in enumerate(filenames):
    with open(path, "r") as f:
        s = f.read()
        _, edges = get_gt_graph_from_comments(s)
        edges = set([(strip_apostrophe(x), strip_apostrophe(y)) for (x,y) in edges])

        with open(tmp_file, "w") as tmp:
            tmp.write(s + command)

        ret = subprocess.run(f"~/.python/env/pymc3/bin/python3 tmp.py", capture_output=True, shell=True, cwd=folder)
        if ret.returncode != 0:
            print(path)
            print(ret.stderr.decode())
        out = ret.stdout.decode()
        # print(out)

        os.remove(tmp_file)


        # pymc_edges = set(re.findall(r"(\w+) -> (\w+)", out))
        pymc_edges = set(re.findall(r"[\"]*([\w(), ]+)[\"]* -> [\"]*([\w(), ]+)[\"]*", out))
        # for (x, y) in pymc_eges:
        #     print(f"# '{x}' -> '{y}'")

        if edges != pymc_edges:
            print(f"{i}.", bcolors.FAIL + path + bcolors.ENDC)
            print("static edges:", sorted(list(edges)))
            print(" pymc3 edges:", sorted(list(pymc_edges)))
            print("static\pymc3:", edges.difference(pymc_edges))
            print("pymc3\static:", pymc_edges.difference(edges))

        else:
            print(f"{i}.", bcolors.OKGREEN + path + bcolors.ENDC)