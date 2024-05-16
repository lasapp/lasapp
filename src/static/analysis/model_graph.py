
from collections import deque
import graphviz
import lasapp
from .utils import is_descendant

class Plate():
    def __init__(self, control_dep):
        self.control_dep = control_dep
        self.members = set() # node_id or Plate

class ModelGraph():
    def __init__(self, random_variables, plates, edges):
        self.random_variables = random_variables # Dict: Id -> RandomVariable
        self.plates = plates                    # Dict: Id -> Plate
        self.edges = edges                      # List: Pair(RandomVariable, RandomVariable)

def get_model_graph(program: lasapp.ProbabilisticProgram):
    model = program.get_model()
    return get_graph(program, model)

def get_guide_graph(program: lasapp.ProbabilisticProgram):
    guide = program.get_guide()
    return get_graph(program, guide)

from functools import cmp_to_key
def get_graph(program: lasapp.ProbabilisticProgram, model):
    call_graph = program.get_call_graph(model.node)
    call_graph_nodes = {n.caller for n in call_graph}

    all_variables = program.get_random_variables()
    # get all random variables in file that are reachable from model
    random_variables = {rv.node.node_id: rv for rv in all_variables if any(is_descendant(call_graph_node, rv.node) for call_graph_node in call_graph_nodes)}

    edges = []
    plates = {"global": Plate(None)}

    for _, rv in random_variables.items():
        marked = set()
        # we recursively get all data and control dependencies of random variable node
        queue = deque([rv.address_node, rv.distribution.node])

        while len(queue) > 0:
            # get next node, FIFO
            node = queue.popleft()

            # get all data dependencies
            data_deps = program.get_data_dependencies(node)

            for dep in data_deps:
                # check if we have already processed node
                if dep.node_id not in marked:
                    if dep.node_id in random_variables:
                        # if node is random variable, we do not continue recursion and add edge to graph
                        dep_rv = random_variables[dep.node_id]
                        edges.append((dep_rv, rv))

                        queue.append(dep_rv.address_node)
                        marked.add(dep_rv.address_node.node_id)
                    else:
                        queue.append(dep)
                    marked.add(dep.node_id)
            
            # get all control dependencies, this are loop / if nodes
            for dep in program.get_control_dependencies(node):
                # get data dependencies of condition / loop variable (control subnode) of control node
                if dep.control_node.node_id not in marked:
                    queue.append(dep.control_node)
                    marked.add(dep.control_node.node_id)
                    

    # compute plates from control_parents
    for _, rv in random_variables.items():
        control_deps = program.get_control_dependencies(rv.node)
        control_deps = sorted(control_deps, key=cmp_to_key(lambda c1, c2: is_descendant(c1.node, c2.node)))
        current_plate = plates["global"]
        for dep in control_deps:
            if dep.kind == "for":
                dep_node_id = dep.node.node_id
                if dep_node_id not in plates:
                    plates[dep_node_id] = Plate(dep)
                current_plate.members.add(plates[dep_node_id])
                current_plate = plates[dep_node_id]

        current_plate.members.add(rv.node.node_id)


    return ModelGraph(random_variables, plates, edges)

def merge_nodes_by_name(model_graph):
    name_to_rvs = {}
    for i, rv in model_graph.random_variables.items():
        if rv.name not in name_to_rvs:
            name_to_rvs[rv.name] = []
        name_to_rvs[rv.name].append(rv)

    for _, rvs in name_to_rvs.items():
        replace_with = rvs[0]
        if len(rvs) > 1 and all(rv.distribution.name == replace_with.distribution.name for rv in rvs[1:]):
            for rv in rvs[1:]:
                del model_graph.random_variables[rv.node.node_id]

                for i, edge in enumerate(model_graph.edges):
                    if edge[0] == rv:
                        edge = (replace_with, edge[1])
                        model_graph.edges[i] = edge
                    
                    if edge[1] == rv:
                        model_graph.edges[i] = (edge[0], replace_with)

                for _, plate in model_graph.plates.items():
                    plate.members.discard(rv.node.node_id)

        model_graph.edges = [edge for i, edge in enumerate(model_graph.edges) if not any(edge == edge2 for edge2 in model_graph.edges[i+1:])]


# label_method in ("name", "source")
# "name" uses the random variable name provided by the backend
# "source" uses the source text of the address node
def plot_model_graph(model_graph, filename="model.gv", view=True, label_method="name"):

    def get_graph(plate, graph=None):
        if graph is None:
            graph = graphviz.Digraph(
                name='cluster_'+plate.control_dep.node.node_id,
                # graph_attr={'label': plate.control_dep["controlsub_node"]["source_text"]}
                )
        
        for m in plate.members:
            if isinstance(m, Plate):
                subgraph = get_graph(m)
                graph.subgraph(subgraph)
            else:
                rv = model_graph.random_variables[m]
                if label_method == "name":
                    label = f"{rv.name}\n~ {rv.distribution.name}"
                elif label_method == "source":
                    label = f"{rv.address_node.source_text}\n~ {rv.distribution.name}"
                else:
                    raise Exception(f"Unknown label method {label_method}")
                # for p in rv.distribution.params:
                #     label += f"\n{p.name} = {p.node.source_text}"
                if rv.is_observed:
                    graph.node(m, label, style="filled", fillcolor="gray")
                else:
                    graph.node(m, label)
        return graph

    dot = graphviz.Digraph('model', engine="dot")
    dot = get_graph(model_graph.plates["global"],graph=dot)

    for x,y in model_graph.edges:
        dot.edge(x.node.node_id, y.node.node_id)

    dot.render(filename=filename, directory='tmp', view=view)
    print(f"Saved graph to tmp/{filename}.pdf")