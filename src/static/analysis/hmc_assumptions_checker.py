
import lasapp
from collections import deque
from .utils import is_descendant

def get_random_control_dependencies(
        program: lasapp.ProbabilisticProgram,
        random_variables: list[lasapp.RandomVariable],
        node: lasapp.SyntaxNode,
        is_control: bool = False # flags if node is already considered part of control (is control_subnode)
    ):
    rv_control_deps = []
    all_deps = {}
    queue = deque([(node, is_control)])

    while len(queue) > 0:
        node, is_control = queue.popleft()

        data_deps = program.get_data_dependencies(node)

        for dep in data_deps:
            if dep.node_id not in all_deps:
                all_deps[dep.node_id] = dep
                if dep.node_id in random_variables:
                    if is_control:
                        rv_control_deps.append(dep)
                else:
                    queue.append((dep, is_control))
        
        for dep in program.get_control_parents(node):
            queue.append((dep.control_subnode, True))

    return rv_control_deps

class HMCAssumptionWarning:
    pass

class ContinuousDistributionViolation(HMCAssumptionWarning):
    def __init__(self, random_variable, distribution):
        self.random_variable = random_variable
        self.distribution = distribution

    def __str__(self) -> str:
        rv_text = self.random_variable.node.source_text#highlight_in_node(rv.node, rv.distribution.node.first_byte, rv.distribution.node.last_byte, "101m")
        s = f"ContinuousDistributionViolation: Distribution type violation in \"{rv_text}\":\n"
        dist_name = self.distribution.name
        s += (f"    {dist_name} distribution is discrete, which is not supported by HMC/NUTS.\n")
        return s

class RandomControlDependentWarning(HMCAssumptionWarning):
    def __init__(self, random_variable, random_control_deps):
        self.random_variable = random_variable
        self.random_control_deps = random_control_deps

    def __str__(self) -> str:
        s = f"RandomControlDependentWarning: Random variable \"{self.random_variable.node.source_text}\" is control dependent on following variables:\n"
        for rv_dep in self.random_control_deps:
            s += f"        {rv_dep.source_text}\n"
        s += "    Random control dependencies may cause discontinuities in the posterior distribution, which are challenging for HMC/NUTS.\n"
        return s

class MultipleDefinitionsWarning(HMCAssumptionWarning):
    def __init__(self, random_variable_name, definitions):
        self.random_variable_name = random_variable_name
        self.definitions = definitions
    
    def __str__(self) -> str:
        return f"MultipleDefinitionsWarning: Multiple definitions ({len(self.definitions)}) for random variable with name {self.random_variable_name}.\n"

class MissingInBranchWarning(HMCAssumptionWarning):
    def __init__(self, random_variable, if_stmt, branch):
        self.random_variable = random_variable
        self.if_stmt = if_stmt
        self.branch = branch

    def __str__(self) -> str:
        s = f"MissingInBranchWarning: Random variable with name {self.random_variable.name} not be defined in program branch.\n"
        s += f"    If condition {self.if_stmt.control_subnode.source_text} may be stochastic and random variable is not defined in {self.branch} branch."
        return s
    
class StochasticForLoopRangeWarning(HMCAssumptionWarning):
    def __init__(self, random_variable, for_stmt):
        self.random_variable = random_variable
        self.for_stmt = for_stmt

    def __str__(self) -> str:
        s = f"StochasticForLoopRangeWarning: Random variable \"{self.random_variable.node.source_text}\" appears in for loop with potentially stochastic range \"{self.for_stmt.control_subnode.source_text}\".\n"
        s += f"    This may lead to an unbounded number of random variables which is not supported by HMC/NUTS."
        return s


class DefinitionInWhileLoopWarning(HMCAssumptionWarning):
    def __init__(self, random_variable, while_stmt):
        self.random_variable = random_variable
        self.while_stmt = while_stmt
    
    def __str__(self) -> str:
        s = f"DefinitionInWhileLoopWarning: Random variable \"{self.random_variable.node.source_text}\" appears in while loop body.\n"
        s += f"    This may lead to an unbounded number of random variables which is not supported by HMC/NUTS."
        return s

class SampleInRecursiveCallWarning(HMCAssumptionWarning):
    def __init__(self, random_variable, function):
        self.random_variable = random_variable
        self.function = function
    
    def __str__(self) -> str:
        s = f"SampleInRecursiveCallWarning: Random variable \"{self.random_variable.node.source_text}\" appears in potentially recursive call.\n"
        s += f"    This may lead to an unbounded number of random variables which is not supported by HMC/NUTS."
        return s
    
def check_hmc_assumptions(program: lasapp.ProbabilisticProgram) -> list[HMCAssumptionWarning]:

    warnings = []

    random_variables = {rv.node.node_id: rv for rv in program.get_random_variables()}

    # check if all variables are continuous
    for _, rv in random_variables.items():
        properties = lasapp.infer_distribution_properties(rv)
        if properties is not None and properties.is_discrete():
            warning = ContinuousDistributionViolation(rv, properties)
            warnings.append(warning)


    # check if a random variable is control dependent on other random variable

    for _, rv in random_variables.items():
        rv_control_deps = get_random_control_dependencies(program, random_variables, rv.node)

        if len(rv_control_deps) > 0:
            warning = RandomControlDependentWarning(rv, rv_control_deps)
            warnings.append(warning)


    # Check if trace is static

    random_variables_per_name = {}
    for _, rv in random_variables.items():
        if rv.name not in random_variables_per_name:
            random_variables_per_name[rv.name] = []
        random_variables_per_name[rv.name].append(rv)
    
    for name, rvs in random_variables_per_name.items():
        if len(rvs) > 1:
            warning = MultipleDefinitionsWarning(name, rvs)
            warnings.append(warning)

        for rv in rvs:
            control_parents = program.get_control_parents(rv.node)
            for control_dep in control_parents:
                if control_dep.kind == "if":
                    # check for stochastic branching
                    if len(get_random_control_dependencies(program, random_variables, control_dep.control_subnode, True)) > 0:
                        # check if variable is defined in other both branches
                        if len(control_dep.body) < 2:
                            warning = MissingInBranchWarning(rv, control_dep, "else")
                            warnings.append(warning)
                        else:
                            appears_in_if_branch = any(is_descendant(control_dep.body[0], rv2.node) for rv2 in rvs)
                            appears_in_else_branch = any(is_descendant(control_dep.body[1], rv2.node) for rv2 in rvs)
                            if not appears_in_if_branch:
                                warning = MissingInBranchWarning(rv, control_dep, "if")
                                warnings.append(warning)
                            if not appears_in_else_branch:
                                warning = MissingInBranchWarning(rv, control_dep, "else")
                                warnings.append(warning)

                if control_dep.kind == "for":
                    # check for stochastic loop range
                    if len(get_random_control_dependencies(program, random_variables, control_dep.control_subnode, True)) > 0:
                        warning = StochasticForLoopRangeWarning(rv, control_dep)
                        warnings.append(warning)
                
                if control_dep.kind == "while":
                    warning = DefinitionInWhileLoopWarning(rv, control_dep)
                    warnings.append(warning)


    # check for sample statements in recursive calls

    model = program.get_model()
    call_graph = program.get_call_graph(model.node)
    call_graph_nodes = {n.caller for n in call_graph}
    
    # call_graph maps caller function to called function (parent to children)
    # invert to map child to parents
    call_graph_parents = {n: [] for n in call_graph_nodes}
    for call_graph_node in call_graph:
        for called in call_graph_node.called:
            call_graph_parents[called].append(call_graph_node.caller)
    
    # get all random variables that appear in syntax node
    def get_random_variable_children(node):
        return [rv for _, rv in random_variables.items() if is_descendant(node, rv.node)]
    
    # recursively checks every call_path of node for cycles
    def has_cyclic_call_path(node, call_path):
        parents = call_graph_parents[node]
        for parent in parents:
            if parent in call_path:
                # parents appears two times in call_path -> cycle
                return True
            else:
                if has_cyclic_call_path(parent, call_path + [parent]):
                    return True                
        return False

    for call_graph_node in call_graph_nodes:
        # get all random variable definitions that appear in node
        child_rvs = get_random_variable_children(call_graph_node)
        if len(child_rvs) > 0:
            # check if node has any call path that is cyclic
            if has_cyclic_call_path(call_graph_node, []):
                for child_rv in child_rvs:
                    warnings.append(SampleInRecursiveCallWarning(child_rv, call_graph_node))

    return warnings
