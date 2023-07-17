
from collections import deque
import graphviz
import lasapp
from .utils import is_descendant

class Plate():
    def __init__(self, control_node):
        self.control_node = control_node
        self.members = set() # node_id or Plate

class ModelGraph():
    def __init__(self, random_variables, plates, edges):
        self.random_variables = random_variables # Dict: Id -> RandomVariable
        self.plates = plates                    # Dict: Id -> Plate
        self.edges = edges                      # List: Pair(RandomVariable, RandomVariable)

def get_model_graph(program: lasapp.ProbabilisticProgram):

    model = program.get_model()
    call_graph = program.get_call_graph(model.node)
    call_graph_nodes = {n.caller for n in call_graph}

    all_variables = program.get_random_variables()
    # get all random variables in file that are reachable from model
    random_variables = {rv.node.node_id: rv for rv in all_variables if any(is_descendant(call_graph_node, rv.node) for call_graph_node in call_graph_nodes)}

    edges = []
    plates = {"global": Plate(None)}

    for _, rv in random_variables.items():
        all_deps = {}
        # we recursively get all data and control dependencies of random variable node
        queue = deque([rv.node])

        while len(queue) > 0:
            # get next node, FIFO
            node = queue.popleft()

            # get all data dependencies
            data_deps = program.get_data_dependencies(node)

            for dep in data_deps:
                # check if we have already processed node
                if dep.node_id not in all_deps:
                    if dep.node_id in random_variables:
                        # if node is random variable, we do not continue recursion and add edge to graph
                        edges.append((random_variables[dep.node_id], rv))
                    else:
                        # if node is not a random variable, we add node to queue to process later
                        queue.append(dep)
                    # mark node as processed
                    all_deps[dep.node_id] = dep
            
            # get all control dependencies, this are loop / if nodes
            for dep in program.get_control_parents(node):
                # get data dependencies of condition / loop variable (control subnode) of control node
                queue.append(dep.control_subnode)


    # compute plates from control_parents
    for _, rv in random_variables.items():
        control_deps = program.get_control_parents(rv.node)
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


def plot_model_graph(model_graph, view=True):

    def get_graph(plate, graph=None):
        if graph is None:
            graph = graphviz.Digraph(
                name='cluster_'+plate.control_node.node.node_id,
                # graph_attr={'label': plate.control_node["controlsub_node"]["source_text"]}
                )
        
        for m in plate.members:
            if isinstance(m, Plate):
                subgraph = get_graph(m)
                graph.subgraph(subgraph)
            else:
                rv = model_graph.random_variables[m]
                label = f"{rv.name}\n~ {rv.distribution.name}"
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

    dot.render(directory='tmp', view=view)
    print("Saved graph to tmp/model.gv.pdf")