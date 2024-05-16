import math
import typing
from collections import deque
from ast_utils.utils import get_call_name
from ast_utils.scoped_tree import ScopedTree, Assignment, FunctionDefinition
from analysis.data_control_flow import *
from copy import copy

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

def usub(x: Interval) -> Interval:
    return Interval(-x.high, -x.low)

def mul(x: Interval, y: Interval) -> Interval:
    E = [x.low * y.low, x.low * y.high, x.high * y.low, x.high * y.high]
    E = [e for e in E if not math.isnan(e)]
    return Interval(min(E), max(E))

def div(x: Interval, y: Interval) -> Interval:
    if y.low == -math.inf and y.high == math.inf:
        # 1/y.high, 1/y.low == 0, 0
        return Interval(-math.inf, math.inf)
    
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
        if y.low == y.high:
            n = y.low
        else:
            return Interval(0, math.inf)
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

def invlogit(x: Interval) -> Interval:
    return Interval(0, 1)

def eq(x: Interval, y: Interval) -> Interval:
    return Interval(0, 1)

def no_op(x: Interval, *args) -> Interval:
    return x

def clip(x: Interval, a: Interval, b:Interval) -> Interval:
    return Interval(a.low, b.high)

def erf(x: Interval) -> Interval:
    return Interval(-1, 1)

def ones(*args) -> Interval:
    return Interval(1.,1.)

def prod(x: Interval) -> Interval:
    # x is array
    if 0 <= x.low and x.high <= 1:
        return Interval(0.,1.) # product of aribtrary many 0<=x<=1 is in [0,1]
    return Interval(-math.inf,math.inf)

# Identity Matrix
def eye(*args) -> Interval:
    return Interval(0.,1.)

import ast

SYMBOL_TO_FUNC = {
    ast.Add: add,
    ast.Sub: sub,
    ast.USub: usub,
    ast.Mult: mul,
    ast.Div: div,
    ast.Pow: pow,
    'sqrt': sqrt,
    'exp': exp,
    'log': log,
    'maximum': maximum,
    'minimum': minimum,

    # pytensor
    'ifelse': ifelse,
    'switch': ifelse,
    'invlogit': invlogit,
    'outer': mul, # outer product
    'eq': eq,
    'flatten': no_op,
    'stack': no_op,
    'reshape': no_op,
    'repeat': no_op,
    'clip': clip,
    'erf': erf,
    'ones': ones,
    'prod': prod,
    'constant': no_op, # pm.math.constant
    'eye': eye,
}

from functools import reduce

class StaticIntervalEvaluator(ast.NodeVisitor):
    def __init__(self, valuation: dict[str, Interval]):
        super().__init__()
        self.valuation = valuation

    def visit(self, node: ast.AST) -> Interval:
        if isinstance(node, (ast.Constant, ast.List, ast.Name, ast.Subscript, ast.UnaryOp, ast.BinOp, ast.Call, ast.Attribute, ast.Return)):
            return super().visit(node)
        if isinstance(node, ast.Expr):
            return self.visit(node.value)
        print(f"Encountered unsupported node {node}: {ast.unparse(node)}")
        return Interval(-math.inf, math.inf)
        
    def visit_Constant(self, node: ast.Constant) -> Interval:
        # Build intervals from constants.
        return Interval(node.value)
    
    def visit_List(self, node: ast.List) -> Interval:
        if len(node.elts) == 0:
            return Interval(-math.inf, math.inf)
        else:
            # one interval for all elements
            return reduce(union, [self.visit(arg) for arg in node.elts])
    
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
    
    def visit_UnaryOp(self, node: ast.UnaryOp) -> Interval:
        operand = self.visit(node.operand)
        func = SYMBOL_TO_FUNC[type(node.op)]
        return func(operand)

    
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
        elif call_name == 'array' and isinstance(node.args[0], ast.List):
            # np array literal
            list = node.args[0]
            return self.visit(list)
        else:
            print(f"Unsupported function {call_name}.")
            # overapproximate as arbitary real number
            return Interval(-math.inf, math.inf)  
        
    def visit_Attribute(self, node: ast.Attribute) -> Interval:
        if node.attr == 'shape':
            # np shape
            return Interval(0, math.inf)
        elif node.attr == 'T':
            # transpose
            return self.visit(node.value)
        else:
            print(f"Warning: Unknown attribute {node.attr} encountered.")
            return Interval(-math.inf, math.inf)
        
    def visit_Return(self, node: ast.Return) -> Interval:
        return self.visit(node.value)


def _static_interval_eval(scoped_tree: ScopedTree, node_to_evaluate: ast.AST, valuation: typing.Dict[str, Interval]):
    identifiers = get_identifiers_read_in_syntaxnode(scoped_tree, node_to_evaluate)
    _, cfgnode = scoped_tree.get_cfgnode_for_syntaxnode(node_to_evaluate)
    
    # update valuation by trying to estimate interval for each identifier read in syntaxnode
    for identifier in identifiers:
        identifier_name = identifier.id
        if identifier_name not in valuation:
            is_function, function = maybe_get_user_function(scoped_tree, identifier)
            if is_function:
                # we estimate the interval of return expression for *any* input
                cfg = scoped_tree.get_cfg_for_function_syntaxnode(function.node)
                intervals = [
                    _static_interval_eval(scoped_tree, get_return_expr(cfgnode), valuation)
                    for cfgnode in cfg.nodes if isinstance(cfgnode, ReturnNode)
                ]
                valuation[identifier_name] = reduce(union, intervals)
            else:
                rds = get_RDs(scoped_tree, cfgnode, identifier)
                if len(rds) > 0:
                    intervals = []
                    for rd in rds:
                        if isinstance(rd, AssignNode):
                            assert isinstance(rd.syntaxnode, ast.Assign), f"Unsupported assign node {rd.syntaxnode}"
                            rhs = rd.syntaxnode.value
                            intervals.append(_static_interval_eval(scoped_tree, rhs, valuation))
                        else: # we do not evaluate
                            intervals.append(Interval(-math.inf, math.inf))
                    valuation[identifier_name] = reduce(union, intervals)

    return StaticIntervalEvaluator(valuation).visit(node_to_evaluate)


# Assumptions: SSA and only elementary functions -> all definitions in same scope
# Only exception: one assignment per if branch
# Elements of array all have same interval
def static_interval_eval(scoped_tree: ScopedTree, node_to_evaluate: ast.AST, valuation: typing.Dict[str, Interval]) ->Interval:
    try:
        return _static_interval_eval(scoped_tree, node_to_evaluate, valuation)
    except RecursionError as e:
        # we could catch recusion already in _static_interval_eval, but this is simpler
        return Interval(-math.inf, math.inf)
