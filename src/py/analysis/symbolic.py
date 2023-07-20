import ast
import typing
from ast_utils.utils import get_call_name, Block
import copy

class SymbolicExpression:
    pass

class Operation(SymbolicExpression):
    def __init__(self, op, *args) -> None:
        self.op = op
        self.args = args
    def __repr__(self) -> str:
        if len(self.args) == 1:
            return f"{self.op}{self.args[0]}"
        if len(self.args) == 2:
            return f"({self.args[0]} {self.op} {self.args[1]})"
        s = ", ".join([str(arg) for arg in self.args])
        return f"{self.op}({s})"
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Operation):
            return False
        return (self.op == other.op and 
                len(self.args) == len(other.args) and 
                all(a == b for (a,b) in zip(self.args, other.args))
                )
def Not(operation: Operation):
    if isinstance(operation, Operation):
        if operation.op == "!":
            return operation.args[0]
    return Operation("!", operation)

class Symbol(SymbolicExpression):
    def __init__(self, name, type="Real") -> None:
        self.name = name
        self.type = type
    def __repr__(self) -> str:
        return self.name
        # return f"{self.type}({self.name})"
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Symbol):
            return False
        return self.name == other.name and self.type == other.type

# s = Type(Name)
def Symbol_from_str(s: str) -> Symbol:
    t, _, n = s[:-1].partition("(")
    return Symbol(n, t)
    
class Constant(SymbolicExpression):
    def __init__(self, value) -> None:
        self.value = value
    def __repr__(self) -> str:
        return f"{self.value}"
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Constant):
            return False
        return self.value == other.value
    
def path_condition_to_str(expr: SymbolicExpression):
    if isinstance(expr, Constant):
        return f"Constant({expr.value})"
    elif isinstance(expr, Symbol):
        return f"{expr.type}({expr.name})"
    else:
        assert isinstance(expr, Operation)
        s = ",".join([path_condition_to_str(arg) for arg in expr.args])
        return f"{expr.op}({s})"

_SYM_AST_NODE_TO_OP = {
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.Div: "/",
    ast.Pow: "^",
    ast.And: "&",
    ast.Or: "|",
    ast.Not: "!",
    ast.USub: "-",
    ast.Eq: "==",
    ast.NotEq: "!=",
    ast.Gt: ">",
    ast.GtE: ">=",
    ast.Lt: "<",
    ast.LtE: "<="
}

class SymbolicEvaluator(ast.NodeVisitor):
    def __init__(self, result, root_node, node_to_symbol) -> None:
        super().__init__()
        self.result = result # Dict: Node -> [PathCondition], keys are all nodes for which we want pathconditions
        self.root_node = root_node
        self.node_to_symbol = node_to_symbol # nodes we want to mask with symbol
        self.name_to_symbol = {} # # dict to store symbolic evaluations of assignments
        self.path_condition = [] # # keeps track of all branching conditions
        self.path = {} # # keeps track of branching choice


    def visit_FunctionDef(self, node: ast.FunctionDef):
        # mask parameters as symbols
        # does not support keyword arguments for now
        for arg in node.args.args:
            name = arg.arg
            sym = Symbol(name)
            if hasattr(arg, 'annotation') and isinstance(arg.annotation, ast.Name):
                if arg.annotation.id == 'bool':
                    sym.type = 'Bool'
                elif arg.annotation.id == 'int':
                    sym.type = 'Int'
            # add to name_to_symbol
            self.name_to_symbol[name] = sym

        # traverse function body
        for stmt in node.body:
            self.visit(stmt)

    
    def visit_If(self, node: ast.If):
        test = self.visit(node.test)

        if node in self.path:
            # we have already a choice for this if statement
            choice = self.path[node]

            res = None
            # follow the choice
            if choice: # (eval)
                # add if condition to path condition
                self.path_condition.append(test)
                # evaluate then branch
                res = self.visit(node.body)
            else:
                # add negated if condition to path condition
                self.path_condition.append(Not(test))
                # evaluate else branch if present
                if hasattr(node, "orelse"):
                    res = self.visit(node.orelse)
            return res

        assert node not in self.path

        # we do not have a choice for this if statement

        # fork the evaluation
        fork_path = copy.copy(self.path)
        fork_path[node] = False # fork evaluator will explore else branch
        fork = SymbolicEvaluator(
            self.result,
            self.root_node,
            self.node_to_symbol
        )
        fork.path = fork_path

        self.path[node] = True # this evaluator will explore then branch

        assert self.path[node] != fork.path[node]

        # start fork from root node
        fork.visit(fork.root_node) # jumps to (eval)

        # continue visiting if statement by following then branch
        self.visit_If(node) # jumps to (eval)

    def visit(self, node):
        if node in self.result:
            # encounterd a node for which we want to evaluate the path_condition
            self.result[node].append(self.path_condition)
            
        if node in self.node_to_symbol:
            # encounterd a node which we want to mask with symbol
            if isinstance(node, ast.Assign):
                # hack for now node is an assignment x = <masked>
                # we map target x to mask symbol in name_to_symbol
                assert len(node.targets) == 1
                target = node.targets[0]
                assert isinstance(target, ast.Name)
                name = target.id
                assert name not in self.node_to_symbol # only one assignment per name
                self.name_to_symbol[name] = self.node_to_symbol[node]
            # return mask symbol
            return self.node_to_symbol[node]
        
        if isinstance(node, (ast.FunctionDef, ast.If, Block, ast.Assign, ast.Constant, ast.Name, ast.UnaryOp, ast.BinOp, ast.BoolOp, ast.Compare, ast.Call)):
            return super().visit(node)
        if isinstance(node, ast.Expr):
            return self.visit(node.value)
        print(f"Encountered unsupported node {node}")

    def visit_Block(self, node: Block):
        # iterate over each statement in block, return last result
        res = None
        for stmt in node:
            res = self.visit(stmt)
        return res
        
    def visit_Assign(self, node: ast.Assign):
        assert len(node.targets) == 1
        target = node.targets[0]
        assert isinstance(target, ast.Name)
        name = target.id
        assert name not in self.node_to_symbol # only one assignment per name
        # symbolically evaluate right hand side
        value = self.visit(node.value)
        # map name to evaluation
        self.name_to_symbol[name] = value
    
    def visit_Constant(self, node: ast.Constant):
        # simply evaluates to constant
        return Constant(node.value)
    
    def visit_Name(self, node: ast.Name):
        # identifier has to be evaluated and stored before
        name = node.id
        assert name in self.name_to_symbol, (name, self.name_to_symbol)
        # return symbolic evaluation for this identifier
        return self.name_to_symbol[name]


    # map function calls to symbolic operation

    def visit_UnaryOp(self, node: ast.UnaryOp):
        operand = self.visit(node.operand)
        assert type(node.op) in _SYM_AST_NODE_TO_OP
        return Operation(_SYM_AST_NODE_TO_OP[type(node.op)], operand)

    def visit_BinOp(self, node: ast.BinOp):
        left = self.visit(node.left)
        right = self.visit(node.right)
        
        assert type(node.op) in _SYM_AST_NODE_TO_OP
        return Operation(_SYM_AST_NODE_TO_OP[type(node.op)], left, right)
    
    def visit_BoolOp(self, node: ast.BinOp):
        values = [self.visit(v) for v in node.values]
        
        assert type(node.op) in _SYM_AST_NODE_TO_OP
        return Operation(_SYM_AST_NODE_TO_OP[type(node.op)], *values)
    
    def visit_Compare(self, node: ast.Compare):
        assert len(node.comparators) == 1 # no chained operations
        left = self.visit(node.left)
        right = self.visit(node.comparators[0])
        op = node.ops[0]
        assert type(op) in _SYM_AST_NODE_TO_OP
        return Operation(_SYM_AST_NODE_TO_OP[type(op)], left, right)
    
    def visit_Call(self, node: ast.Call):
        name = get_call_name(node)
        values = [self.visit(arg) for arg in node.args]
        return Operation(name, *values)

# We will collect multiple path conditions that can be combined by following rule
# (A and B and ...) or (!A and B and ...) => B and ...
def combine_paths(paths):
    new_paths = []
    for path_condition in paths:
        # we try to find a second path in new_paths which we can use to combine
        # we keep trying until there is no path in new_paths to combine with
        pc = copy.deepcopy(path_condition)
        while True:
            did_change = False
            for i in range(len(new_paths)):
                other_pc = new_paths[i]
                if len(other_pc) != len(pc):
                    continue
                # Not(A) and A have to be exactly at same index in path condition
                # correspond to same if statement
                matching = 0
                index = None
                for j in range(len(pc)):
                    if pc[j] == Not(other_pc[j]):
                        index = j
                    if pc[j] == other_pc[j]:
                        matching += 1

                if matching == len(pc)-1 and index is not None:
                    # found a matching path 
                    del new_paths[i] # remove other_pc
                    del pc[index] # (A and B and ...) or (!A and B and ...) => B and ...
                    did_change = True
                    break

            if not did_change:
                break
        
        new_paths.append(pc)

    new_paths = [path for path in new_paths if len(path) > 0]

    if len(new_paths) == 0:
        return Constant(True)
    if len(new_paths) == 1:
        path = new_paths[0]
        return path[0] if len(path) == 1 else Operation("&", *path) 
    
    return Operation("|", *[path[0] if len(path) == 1 else Operation("&", *path) for path in new_paths])

def get_path_condition_for_nodes(func: ast.FunctionDef, nodes: typing.List[ast.AST], node_to_symbol: typing.Dict[ast.AST, Symbol]):
    result = {node: [] for node in nodes}
    evaluator = SymbolicEvaluator(result, func, node_to_symbol)
    evaluator.visit(func)
    result = {node: combine_paths(paths) for node, paths in result.items()}
    return result

