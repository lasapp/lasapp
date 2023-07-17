import z3
import lasapp
import lasapp.distributions as dists
from .utils import is_descendant
from itertools import combinations

class ACViolationWarning:
    pass

class OverlappingSampleStatements(ACViolationWarning):
    def __init__(self, func, rv_name, rv1, pc1, rv2, pc2) -> None:
        self.func = func
        self.rv_name = rv_name
        self.rv1 = rv1
        self.pc1 = pc1
        self.rv2 = rv2
        self.pc2 = pc2
    def __repr__(self) -> str:
        s = f"OverlappingSampleStatements in {self.func} for {self.rv_name}:\n"
        s += f"{self.rv1.node.source_text} in path {self.pc1} and {self.rv2.node.source_text} in path {self.pc2} may be executed at the same time."
        return s
    
class AbsoluteContinuityViolation(ACViolationWarning):
    def __init__(self, rv_name, info) -> None:
        self.rv_name = rv_name
        self.info = info
    def __repr__(self) -> str:
        return f"AbsoluteContinuityViolation:\nSampling {self.rv_name} in model does not imply sampling in guide ({self.info})."
        

class SupportTypeMismatch(ACViolationWarning):
    def __init__(self, rv_name, model_rv, model_pc, guide_rv, guide_pc) -> None:
        self.rv_name = rv_name
        self.model_rv = model_rv
        self.model_pc = model_pc
        self.guide_rv = guide_rv
        self.guide_pc = guide_pc
    def __repr__(self) -> str:
        s = f"SupportTypeMismatch for {self.rv_name} at {self.model_pc} ∧ {self.guide_pc}:\n"
        s += f"Type of model rv {self.model_rv.node.source_text} is not type of guide {self.guide_rv.node.source_text} (or could not be inferred)."
        return s
    
class SupportIntervalMismatch(ACViolationWarning):
    def __init__(self, rv_name, model_rv, model_pc, guide_rv, guide_pc) -> None:
        self.rv_name = rv_name
        self.model_rv = model_rv
        self.model_pc = model_pc
        self.guide_rv = guide_rv
        self.guide_pc = guide_pc
    def __repr__(self) -> str:
        s = f"SupportIntervalMismatch for {self.rv_name} at {self.model_pc} ∧ {self.guide_pc}:\n"
        s += f"Support of model rv {self.model_rv.node.source_text} is not subset of guide rv {self.guide_rv.node.source_text}"
        return s
        

class Operation:
    def __init__(self, name, parent=None) -> None:
        self.name = name
        self.parent = parent
        self.children = []
        if parent is not None:
            parent.children.append(self)
    def __repr__(self) -> str:
        s = self.name + "("
        s += ",".join(str(c) for c in self.children)
        s += ")"
        return s

def parse_path_condition_str(s: lasapp.SymbolicExpression) -> z3.ExprRef:
    # parse grammar:
    # op ::= op(op,...,op)
    # op ::= Real, Int, Bool, Constant, +, -, ...
    root = Operation("root")
    current_word = ""
    current = root
    for char in s.expr:
        if char == "(":
            current = Operation(current_word, parent=current)
            current_word = ""
        elif char == ")":
            if current_word != "":
                current.children.append(current_word)
            current_word = ""
            current = current.parent
        elif char == ",":
            if current_word != "":
                current.children.append(current_word)
            current_word = ""
        else:
            current_word += char

    assert current == root
    # print(root.children[0])

    # now convert to z3 expression
    def minus(x, y=None):
        if y is None:
            return -x
        else:
            return x - y

    z3_symbol_to_variable = {}
    z3_name_to_func = {
        "Real": z3.Real,
        "Int": z3.Int,
        "Bool": z3.Bool,
        "+": lambda x, y: x + y,
        "-": minus,
        "*": lambda x, y: x * y,
        "/": lambda x, y: x / y,
        "^": lambda x, y: x ** y,
        "&": z3.And,
        "|": z3.Or,
        "!": z3.Not,
        "==": lambda x, y: x == y,
        "!=": lambda x, y: x != y,
        ">": lambda x, y: x > y,
        ">=": lambda x, y: x >= y,
        "<": lambda x, y: x < y,
        "<=": lambda x, y: x <= y,
    }
    def to_z3(op: Operation) -> z3.ExprRef:
        if op.name == "Constant":
            assert len(op.children) == 1, op.children
            value = op.children[0]
            assert isinstance(value, str)
            if value.lower() == "true":
                return True
            if value.lower() == "false":
                return False
            return int(value)
        elif op.name in ("Real", "Int", "Bool"):
            assert len(op.children) == 1, op.children
            symbol = op.children[0]
            if symbol in z3_symbol_to_variable:
                variable = z3_symbol_to_variable[symbol]
            else:
                variable = z3_name_to_func[op.name](symbol)
                z3_symbol_to_variable[symbol] = variable
            return variable
        else:
            return z3_name_to_func[op.name](*[to_z3(arg) for arg in op.children])

    return to_z3(root.children[0])

def SymblicExpression(random_variable: lasapp.RandomVariable) -> lasapp.SymbolicExpression:
    properties = dists.infer_distribution_properties(random_variable)
    if properties is None:
        t = "Real"
    # elif properties.name == "Bernoulli":
    #     t = "Bool" # does not handle comparison to integer
    elif properties.is_discrete():
        t = "Int"
    else:
        t = "Real"
    return lasapp.SymbolicExpression(f"{t}({random_variable.name})")

# get path conditions for every variable in terms of input parameters to func and other variables
def get_path_conditions(
        program: lasapp.ProbabilisticProgram,
        model: lasapp.Model,
        variables:list[lasapp.RandomVariable],
        assumptions: dict[lasapp.SyntaxNode, lasapp.SymbolicExpression]) -> dict[lasapp.RandomVariable,z3.ExprRef]:

    nodes = [rv.node for rv in variables]
    path_condition_list = program.get_path_conditions(nodes, model.node, assumptions)
    path_conditions = {}
    for rv, path_condition_str in zip(variables, path_condition_list):
        path_conditions[rv] = parse_path_condition_str(path_condition_str)
    return path_conditions

# return distribution type of RandomVariable: discrete or continuous
def get_type(rv: lasapp.RandomVariable):
    properties = dists.infer_distribution_properties(rv)
    if properties is None:
        return None
    return properties.type

def get_param_with_name(distribution: lasapp.server_interface.Distribution, name: str):
    for param in distribution.params:
        if param.name == name:
            return param
    return None

# tries to infer support in terms of interval for RandomVariable
def get_support_interval(rv: lasapp.RandomVariable):
    properties = dists.infer_distribution_properties(rv)
    if properties is None:
        return None
            
    support_interval = dists.to_interval(properties.support)
    if support_interval is None:
        return None
    
    if isinstance(support_interval.low, str):
        param = get_param_with_name(rv.distribution, support_interval.low)
        if param is None:
            return None
        support_interval.low = float(param.node.source_text)

    if isinstance(support_interval.high, str):
        param = get_param_with_name(rv.distribution, support_interval.high)
        if param is None:
            return None
        support_interval.high = float(param.node.source_text)

    return support_interval


def get_distribution_constraint(random_variable: lasapp.RandomVariable) -> z3.ExprRef:
    rv_support = get_support_interval(random_variable)
    t = get_type(random_variable)
    var = z3.Int(random_variable.name) if t == dists.DistributionType.Discrete else z3.Real(random_variable.name)

    dc = z3.And(True)
    if rv_support.high < float('inf'):
        dc = z3.And(dc, var <= rv_support.high)

    if float('-inf') < rv_support.low:
        dc = z3.And(dc, rv_support.low <= var)

    return dc
    

# checks if program paths of sample statements for rv with same name are disjoint
def check_disjointness(func: str, path_condition: dict[lasapp.RandomVariable, z3.ExprRef], stmts_by_name: dict[str, list[lasapp.RandomVariable]]):
    violations = []
    for name, stmts in stmts_by_name.items():
        # iterate over all pairs of sample statemnts for rv `name`
        for rv1, rv2 in combinations(stmts,2):
            solver = z3.Solver()
            pc1 = path_condition[rv1]
            pc2 = path_condition[rv2]
            solver.add(z3.And(pc1, pc2))
            # check if the both paths are satisfiable at the same time
            if solver.check() == z3.sat:
                # yes -> rv `name` could be sampled twice
                violations.append(OverlappingSampleStatements(func, name, rv1, pc1, rv2, pc2))
    return violations

def group_by_name(random_variables: list[lasapp.RandomVariable]) -> dict[str, list[lasapp.RandomVariable]]:
    result = {rv.name: [] for rv in random_variables}
    for rv in random_variables:
        result[rv.name].append(rv)
    return result


def check_guide(program: lasapp.ProbabilisticProgram):
    violations = []

    random_variables = program.get_random_variables()
    assumptions = {rv.node: SymblicExpression(rv) for rv in random_variables}

    model = program.get_model()
    model_rvs = [rv for rv in random_variables if is_descendant(model.node, rv.node)]
    model_rvs_by_name = group_by_name(model_rvs)

    guide = program.get_guide()
    guide_rvs = [rv for rv in random_variables if is_descendant(guide.node, rv.node)]
    guide_rvs_by_name = group_by_name(guide_rvs)

    # path_condition = {
    #     **{rv: program.get_path_condition(rv.node, model.node, assumptions) for rv in model_rvs},
    #     **{rv: program.get_path_condition(rv.node, guide.node, assumptions) for rv in guide_rvs}
    # }
    # path_condition = {rv: parse_path_condition_str(s) for rv, s in path_condition.items()}

    # batched version
    path_condition = {
        **get_path_conditions(program, model, model_rvs, assumptions),
        **get_path_conditions(program, guide, guide_rvs, assumptions)
    }

    distribution_constraint = {
        rv: get_distribution_constraint(rv) for rv in random_variables
    }

    # check if program paths of sample statements for rv with same name are disjoint
    violations += check_disjointness("model", path_condition, model_rvs_by_name)

    # check if program paths of sample statements for rv with same name are disjoint
    violations += check_disjointness("guide", path_condition, guide_rvs_by_name)

        
    # check if rv X=v is sampled in model implies X=v sample is possible in guide
    for name, model_stmts in  model_rvs_by_name.items():
        if name not in guide_rvs_by_name:
            # there is no sample statement for rv `name` in guide.
            violations.append(AbsoluteContinuityViolation(name, "No sample statement in guide."))
            continue
        guide_stmts = guide_rvs_by_name[name]

        types = [(rv, path_condition[rv], get_type(rv)) for rv in model_stmts] + [(rv, path_condition[rv], get_type(rv)) for rv in guide_stmts]
        type_mismatch = False
        for t1, t2 in combinations(types, 2):
            if t1[2] != t2[2]:
                # types do not match Continuous vs Discrete vs None
                violations.append(SupportTypeMismatch(name, t1[0], t1[1], t2[0], t2[1]))
                type_mismatch = True
        if type_mismatch:
            continue

        # add variable support constraint to path conditions
        model_pcs = [z3.And(path_condition[stmt], distribution_constraint[stmt]) for stmt in model_stmts]
        guide_pcs = [z3.And(path_condition[stmt], distribution_constraint[stmt]) for stmt in guide_stmts]

        solver = z3.Solver()
        impl = z3.Implies(z3.Or(model_pcs), z3.Or(guide_pcs))
        solver.add(z3.Not(impl))
        res = solver.check()
        # if res == z3.unsat then we proved implication
        if res == z3.sat:
            # there is a path in the model such that rv X=v is sampled (with constraints),
            # but for the same path X=v cannot be sampled in guide (with the constraints).
            # i.e. there are rvs with values X_i = v_i such that (X_1=v_1, ..., X_n=v_n, X=v) is a possible
            # execution trace for the model, but not for the guide, p_guide((X_1=v_1, ..., X_n=v_n, X=v)) = 0.
            violations.append(AbsoluteContinuityViolation(name, f"Counterexample: {solver.model()}"))
        elif res == z3.unknown:
            print(f"Warning. Could not prove or disprove {impl} for {name}")

    # More detailed Warnings:

    # if model sample statement and guide statement can be in same path,
    # check if their distributions satisfy absolute continuity
    for name, model_stmts in  model_rvs_by_name.items():
        if name not in guide_rvs_by_name:
            continue
        guide_rv_pcs = guide_rvs_by_name[name]

        for (model_rv) in model_stmts:
            for (guide_rv) in guide_rv_pcs:
                model_pc = path_condition[model_rv]
                guide_pc = path_condition[guide_rv]

                solver = z3.Solver()
                intersect = z3.And(model_pc, guide_pc)
                solver.add(intersect)
                res = solver.check()
                # check if both paths can be satisfied
                if res == z3.sat:
                    # there is an execution trace X_i = v_i, such that
                    # rv X is sampled in both guide and model.
                    # -> check if distribution supports satisfy absolute continuity

                    # compare distribution types first
                    model_rv_type = get_type(model_rv)
                    guide_rv_type = get_type(guide_rv)
                    if model_rv_type is not None and guide_rv_type is not None:
                        if model_rv_type == guide_rv_type:
                            model_rv_support = get_support_interval(model_rv)
                            guide_rv_support = get_support_interval(guide_rv)
                            if model_rv_support is None or guide_rv_support is None:
                                continue
                            if not model_rv_support.is_subset(guide_rv_support):
                                # model support interval is not subset of guide support interval
                                violations.append(SupportIntervalMismatch(name, model_rv, model_pc, guide_rv, guide_pc))

    return violations

#%%