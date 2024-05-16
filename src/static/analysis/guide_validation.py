import z3
import lasapp
import lasapp.distributions as dists
from .utils import is_descendant
from itertools import combinations
from typing import Optional

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
    

class GlobalAbsoluteContinuityViolation(ACViolationWarning):
    def __init__(self, P: lasapp.Model, Q: lasapp.Model, info) -> None:
        self.P = P
        self.Q = Q
        self.info = info
    def __repr__(self) -> str:
        return f"GlobalAbsoluteContinuityViolation:\n Density of {self.P.name} greater than 0 does not imply density of {self.Q.name} greater than 0 ({self.info})."     

class AbsoluteContinuityViolation(ACViolationWarning):
    def __init__(self, P: lasapp.Model, Q: lasapp.Model, rv_name, info) -> None:
        self.P = P
        self.Q = Q
        self.rv_name = rv_name
        self.info = info
    def __repr__(self) -> str:
        return f"AbsoluteContinuityViolation:\nSampling {self.rv_name} in {self.P.name} does not imply sampling in {self.Q.name} ({self.info})."
        

class SupportTypeMismatch(ACViolationWarning):
    def __init__(self, P: lasapp.Model, Q: lasapp.Model, rv_name, P_rv, P_pc, Q_rv, Q_pc) -> None:
        self.P = P
        self.Q = Q
        self.rv_name = rv_name
        self.P_rv = P_rv
        self.P_pc = P_pc
        self.Q_rv = Q_rv
        self.Q_pc = Q_pc
    def __repr__(self) -> str:
        s = f"SupportTypeMismatch for {self.rv_name} at {self.P_pc} ∧ {self.Q_pc}:\n"
        s += f"Support type of {self.P.name} rv {self.P_rv.node.source_text} is not equal to type of {self.Q.name} rv {self.Q_rv.node.source_text} (or could not be inferred)."
        return s
    
class SupportIntervalMismatch(ACViolationWarning):
    def __init__(self, P: lasapp.Model, Q: lasapp.Model, rv_name, P_rv, P_pc, P_rv_support, Q_rv, Q_pc, Q_rv_support) -> None:
        self.P = P
        self.Q = Q
        self.rv_name = rv_name
        self.P_rv = P_rv
        self.P_pc = P_pc
        self.P_rv_support = P_rv_support
        self.Q_rv = Q_rv
        self.Q_pc = Q_pc
        self.Q_rv_support = Q_rv_support
    def __repr__(self) -> str:
        s = f"SupportIntervalMismatch for {self.rv_name} at {self.P_pc} ∧ {self.Q_pc}:\n"
        s += f"Support of {self.P.name} rv {self.P_rv.node.source_text} is not subset of support of {self.Q.name} rv {self.Q_rv.node.source_text} ({self.P_rv_support} vs {self.Q_rv_support})"
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
            # TODO: maybe use only z3.Real
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
        mask: dict[lasapp.SyntaxNode, lasapp.SymbolicExpression]) -> dict[lasapp.RandomVariable,z3.ExprRef]:

    nodes = [rv.node for rv in variables]
    path_condition_list = program.get_path_conditions(nodes, model.node, mask)
    path_conditions = {}
    for rv, path_condition_str in zip(variables, path_condition_list):
        path_conditions[rv] = parse_path_condition_str(path_condition_str)
    return path_conditions

# return distribution type of RandomVariable: discrete or continuous
def get_type(rv: lasapp.RandomVariable):
    properties = dists.infer_distribution_properties(rv)
    assert properties is not None, f"Could not find properties for {rv.node.source_text}"
    return properties.type

def get_support_constraint(rv: lasapp.RandomVariable):
    properties = dists.infer_distribution_properties(rv)
    assert properties is not None, f"Could not find properties for {rv.node.source_text}"
    return properties.support

def get_param_with_name(distribution: lasapp.server_interface.Distribution, name: str):
    for param in distribution.params:
        if param.name == name:
            return param
    return None

# tries to infer support in terms of interval for RandomVariable
def get_support_interval(program: lasapp.ProbabilisticProgram, mask: dict[lasapp.SyntaxNode, lasapp.Interval], rv: lasapp.RandomVariable):
    support_constraint = get_support_constraint(rv)
    support_interval = dists.to_interval(support_constraint)
    if support_interval is None:
        # print(f"Could not get support as interval for {rv.node.source_text}")
        return None

    if isinstance(support_interval.low, dists.ParamDependentBound):
        param = get_param_with_name(rv.distribution, support_interval.low.param)
        assert param is not None, f"No param for {support_interval.low}"
        estimated_range = program.estimate_value_range(
            expr=param.node,
            mask=mask # mask up to now, rvs are sorted
        )
        support_interval.low = float(estimated_range.low)

    if isinstance(support_interval.high, dists.ParamDependentBound):
        param = get_param_with_name(rv.distribution, support_interval.high.param)
        assert param is not None, f"No param for {support_interval.high}"
        estimated_range = program.estimate_value_range(
                    expr=param.node,
                    mask=mask # mask up to now, rvs are sorted
                )
        support_interval.high = float(estimated_range.high)

    return support_interval


def get_distribution_constraint(program: lasapp.ProbabilisticProgram, random_variable: lasapp.RandomVariable) -> Optional[z3.ExprRef]:
    # NOTE: here we assume no mask necessary to obtain support interval (static support)
    # i.e. the support does not depend on other rvs
    rv_support = get_support_interval(program, dict(), random_variable)
    if rv_support is None:
        return None
    
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

def check_proposal(program: lasapp.ProbabilisticProgram):
    model = program.get_model()
    guide = program.get_guide()
    return check_ac(program, model, guide)

def check_svi(program: lasapp.ProbabilisticProgram):
    model = program.get_model()
    guide = program.get_guide()
    return check_ac(program, guide, model)

# checks if P(x) > 0 => Q(x) > 0
# or equivalently if Q(x) = 0 => P(x) = 0
def check_ac(program: lasapp.ProbabilisticProgram, P: lasapp.Model, Q: lasapp.Model):
    violations = []

    random_variables = program.get_random_variables()
    mask = {rv.node: SymblicExpression(rv) for rv in random_variables}

    P_rvs = [rv for rv in random_variables if is_descendant(P.node, rv.node) and not rv.is_observed]
    P_rvs_by_name = group_by_name(P_rvs)

    Q_rvs = [rv for rv in random_variables if is_descendant(Q.node, rv.node) and not rv.is_observed]
    Q_rvs_by_name = group_by_name(Q_rvs)

    # path_condition = {
    #     **{rv: program.get_path_condition(rv.node, P.node, mask) for rv in Q_rvs},
    #     **{rv: program.get_path_condition(rv.node, Q.node, mask) for rv in Q_rvs}
    # }
    # path_condition = {rv: parse_path_condition_str(s) for rv, s in path_condition.items()}

    # batched version
    path_condition = {
        **get_path_conditions(program, P, P_rvs, mask),
        **get_path_conditions(program, Q, Q_rvs, mask)
    }

    distribution_constraint = {
        rv: get_distribution_constraint(program, rv) for rv in random_variables
    }

    solver = z3.Solver()
    impl = z3.Implies(
        z3.And([z3.Implies(path_condition[rv],distribution_constraint[rv]) for rv in P_rvs if distribution_constraint[rv] is not None]),
        z3.And([z3.Implies(path_condition[rv],distribution_constraint[rv]) for rv in Q_rvs if distribution_constraint[rv] is not None]),
    )
    solver.add(z3.Not(impl))
    res = solver.check()
    if res == z3.sat:
        violations.append(GlobalAbsoluteContinuityViolation(P, Q, f"Counterexample: {solver.model()}"))
    # (1) More detailed Warnings: (this is not part of the paper, see supplementary material)

    # check if program paths of sample statements for rv with same name are disjoint
    violations += check_disjointness(P.name, path_condition, P_rvs_by_name)

    # check if program paths of sample statements for rv with same name are disjoint
    violations += check_disjointness(Q.name, path_condition, Q_rvs_by_name)
        
    # check if rv X=v is sampled in model implies X=v sample is possible in Q
    for name, P_stmts in  P_rvs_by_name.items():
        if name not in Q_rvs_by_name:
            # there is no sample statement for rv `name` in Q.
            violations.append(AbsoluteContinuityViolation(P, Q, name, f"No sample statement in {Q.name}"))
            continue
        Q_stmts = Q_rvs_by_name[name]

        if any(distribution_constraint[stmt] is None for stmt in P_stmts + Q_stmts):
            continue # handled in (1)

        # add variable support constraint to path conditions
        P_pcs = [z3.And(path_condition[stmt], distribution_constraint[stmt]) for stmt in P_stmts]
        Q_pcs = [z3.And(path_condition[stmt], distribution_constraint[stmt]) for stmt in Q_stmts]

        solver = z3.Solver()
        impl = z3.Implies(z3.Or(P_pcs), z3.Or(Q_pcs))
        solver.add(z3.Not(impl))
        res = solver.check()
        # if res == z3.unsat then we proved implication
        if res == z3.sat:
            # there is a path in P such that rv X=v is sampled (with constraints),
            # but for the same path X=v cannot be sampled in Q (with the constraints).
            # i.e. there are rvs with values X_i = v_i such that (X_1=v_1, ..., X_n=v_n, X=v) is a possible
            # execution trace for P, but not for Q, p_Q((X_1=v_1, ..., X_n=v_n, X=v)) = 0.
            violations.append(AbsoluteContinuityViolation(P, Q, name, f"Counterexample: {solver.model()}"))
        elif res == z3.unknown:
            print(f"Warning: Could not prove or disprove {impl} for {name}")

    # if model sample statement and Q statement can be in same path,
    # check if their distributions satisfy absolute continuity
    for name, P_stmts in  P_rvs_by_name.items():
        if name not in Q_rvs_by_name:
            continue
        Q_rv_pcs = Q_rvs_by_name[name]

        for (P_rv) in P_stmts:
            for (Q_rv) in Q_rv_pcs:
                P_pc = path_condition[P_rv]
                Q_pc = path_condition[Q_rv]

                solver = z3.Solver()
                intersect = z3.And(P_pc, Q_pc)
                solver.add(intersect)
                res = solver.check()
                # check if both paths can be satisfied
                if res == z3.sat:
                    # there is an execution trace X_i = v_i, such that
                    # rv X is sampled in both Q and P.
                    # -> check if distribution supports satisfy absolute continuity

                    # compare distribution types first
                    P_rv_type = get_type(P_rv)
                    Q_rv_type = get_type(Q_rv)
                    P_rv_constraint = get_support_constraint(P_rv)
                    Q_rv_constraint = get_support_constraint(Q_rv)

                    if P_rv_type == Q_rv_type and isinstance(P_rv_constraint, dists.IntervalConstraint) == isinstance(Q_rv_constraint, dists.IntervalConstraint):
                        P_rv_support = get_support_interval(program, dict(), P_rv)
                        Q_rv_support = get_support_interval(program, dict(), Q_rv)
                        if P_rv_support is None or Q_rv_support is None:
                            continue
                        if not P_rv_support.is_subset_of(Q_rv_support):
                            # model support interval is not subset of Q support interval
                            violations.append(SupportIntervalMismatch(P, Q, name, P_rv, P_pc, P_rv_support, Q_rv, Q_pc, Q_rv_support))

                    elif P_rv_type != Q_rv_type or P_rv_constraint != Q_rv_constraint:
                        violations.append(SupportTypeMismatch(P, Q, name, P_rv, P_pc, Q_rv, Q_pc))

    return violations
