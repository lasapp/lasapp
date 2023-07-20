import math
import typing
from collections import deque
from ast_utils.utils import get_call_name
from ast_utils.scoped_tree import ScopedTree, Assignment
from analysis.data_control_flow import *

class Interval:
    def __init__(self, low: float, high: float = None) -> None:
        self.low = low        
        self.high = high if high is not None else low
    def __repr__(self):
        return f"[{self.low}, {self.high}]"
    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Interval):
            return False
        else:
            return self.low == __value.low and self.high == __value.high

def add(x: Interval, y: Interval) -> Interval:
    return Interval(x.low + y.low, x.high + y.high)

def sub(x: Interval, y: Interval) -> Interval:
    return Interval(x.low - y.high, x.high - y.low)

def mul(x: Interval, y: Interval) -> Interval:
    E = [x.low * y.low, x.low * y.high, x.high * y.low, x.high * y.high]
    E = [e for e in E if not math.isnan(e)]
    return Interval(min(E), max(E))

def div(x: Interval, y: Interval) -> Interval:
    if y.low != 0 and y.high != 0:
        y = Interval(1/y.high, 1/y.low)
    elif y.low != 0:
        y = Interval(-math.inf, 1/y.low)
    elif y.high != 0:
        y = Interval(1/y.high, math.inf)
    else:
        raise ValueError("Division by zero.")
    
    return mul(x, y)

def pow(x: Interval, y: Interval) -> Interval:
    if isinstance(y, Interval):
        assert y.low == y.high
        n = y.low
    n == y

    if n % 2 != 0:
        return Interval(x.low ** n, x.high ** n)
    else:
        if x.low >= 0:
            return Interval(x.low ** n, x.high ** n)
        else:
            return Interval(0., x.high ** n)


def minimum(x: Interval, y: Interval) -> Interval:
    return Interval(min(x.low, y.low), min(x.high, y.high))

def maximum(x: Interval, y: Interval) -> Interval:
    return Interval(max(x.low, y.low), max(x.high, y.high))

def sqrt(x: Interval) -> Interval:
    return Interval(math.sqrt(x.low), math.sqrt(x.high))

def log(x: Interval) -> Interval:
    low = math.log(x.low) if x.low != 0 else -math.inf
    high = math.log(x.high) if x.high != 0 else -math.inf

    return Interval(low, high)

def exp(x: Interval) -> Interval:
    return Interval(math.exp(x.low), math.exp(x.high))

def union(x: Interval, y: Interval) -> Interval:
    return Interval(min(x.low, y.low), max(x.high, y.high)) # over-approximate if disjoint
    
def ifelse(test: Interval, x: Interval, y: Interval) -> Interval:
    return union(x, y)

import ast

SYMBOL_TO_FUNC = {
    ast.Add: add,
    ast.Sub: sub,
    ast.Mult: mul,
    ast.Div: div,
    ast.Pow: pow,
    'sqrt': sqrt,
    'exp': exp,
    'log': log,
    'maximum': maximum,
    'minimum': minimum,

    'ifelse': ifelse, # pytensor
}
    
class StaticIntervalEvaluator(ast.NodeVisitor):
    def __init__(self, valuation: dict[str, Interval]):
        super().__init__()
        self.valuation = valuation

    def visit(self, node: ast.AST) -> Interval:
        if isinstance(node, (ast.Constant, ast.Name, ast.Subscript, ast.BinOp, ast.Call)):
            return super().visit(node)
        if isinstance(node, ast.Expr):
            return self.visit(node.value)
        print(f"Encountered unsupported node {node}")
        
    def visit_Constant(self, node: ast.Constant) -> Interval:
        # Build intervals from constants.
        return Interval(node.value)
    
    def visit_Name(self, node: ast.Name) -> Interval:
        if node.id in self.valuation:
            # return current interval valuation for identifier
            return self.valuation[node.id]
        else:
            # no valuation for identifier found -> overapproximate as arbitary real number
            print(f"Warning: Unknown symbol {node.id} encountered.")
            return Interval(-math.inf, math.inf)
        
    def visit_Subscript(self, node: ast.Subscript) -> Interval:
        # # array elements are all masked as one interval
        return self.visit(node.value)
    
    def visit_BinOp(self, node: ast.BinOp) -> Interval:
        left = self.visit(node.left)
        right = self.visit(node.right)
        func = SYMBOL_TO_FUNC[type(node.op)]
        return func(left, right)
    
    def visit_Call(self, node: ast.Call) -> Interval:
        # map call to interval arithmetic operation

        call_name = get_call_name(node)
        if call_name in self.valuation:
            # functions can also be masked
            return self.valuation[call_name]

        if call_name in SYMBOL_TO_FUNC:
            func = SYMBOL_TO_FUNC[call_name]

            values = [self.visit(arg) for arg in node.args]
            if (len(node.args) == 0 or
                (call_name in ('maximum', 'minimum') and len(node.args) == 1)):
                # support x.exp(), etc
                assert isinstance(node.func, ast.Attribute)
                values.insert(0, self.visit(node.func.value))

            # # evaluate interval operation
            return func(*values)
                
        else:
            print(f"Unsupported function {call_name}.")
            # overapproximate as arbitary real number
            return Interval(-math.inf, math.inf)  

# Assumptions: SSA and only elementary functions -> all definitions in same scope
# Only exception: one assignment per if branch
# Elements of array all have same interval
def static_interval_eval(scoped_tree: ScopedTree, node_to_evaluate: ast.AST, valuation: typing.Dict[str, Interval]) -> Interval:
    # get all data dependencies by recursively calling and traversing data_deps_for_node
    # should be only assingments
    data_deps = set() # Assignment
    nodes = deque([node_to_evaluate])
    while len(nodes) > 0:
        node = nodes.popleft()
        for dep in data_deps_for_node(scoped_tree, node):
            if dep not in data_deps:
                if dep.name not in valuation: # otherwise already abstracted away
                    assert isinstance(dep, Assignment)
                    data_deps.add(dep)
                    nodes.append(dep.node)

    # list of assignments in sequential order
    data_deps = sorted(data_deps, key=lambda x: x.id)

    # statically evaluate in sequential order
    tmp_valuation = {}
    evaluator = StaticIntervalEvaluator(valuation)

    for (i, dep) in enumerate(data_deps):
        assert isinstance(dep.node, ast.Assign)

        rhs = dep.node.value

        res = evaluator.visit(rhs)

        if dep.name in valuation:
            # multiple assignments
            # should only happen if assignments are in different branches
            # this over-approximates resulting set (union of intervals) as interval
            # this is used after if branches, i.e. last time dep.name was assigned (lexicographically)
            if dep.name not in tmp_valuation:
                tmp_valuation[dep.name] = valuation[dep.name]
            tmp_valuation[dep.name] = union(res, tmp_valuation[dep.name])

        valuation[dep.name] = res # (is used also by evaluator)

        if dep.name in tmp_valuation:
            if not any(future_dep.name == dep.name for future_dep in data_deps[i+1:]):
                # we reached last (of multiple) assignment of dep.name
                # we now write the over-approximation (union of intervals of all assignments)
                valuation[dep.name] = tmp_valuation[dep.name]
    
    # lastly, evaluate node where all dependencies are masked with their intervals
    res = evaluator.visit(node_to_evaluate)

    return res