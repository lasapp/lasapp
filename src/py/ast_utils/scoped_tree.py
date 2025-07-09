import ast
from typing import Any, Union
import ast_scope
from ast_utils.node_finder import NodeFinder
from ast_utils.node_finders import get_user_defined_functions
from ast_utils.preprocess import SyntaxTree
from ast_utils.utils import get_name, is_descendant
from ast_utils.cfg import *

class Assignment:
    def __init__(self, node: ast.Assign, identifier: ast.Name, id: int):
        assert isinstance(node, ast.Assign)
        assert len(node.targets) == 1
        self.node = node
        self.id = id
        self.identifier = identifier
        self.name = self.identifier.id # str


class AssignmentCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.assignments = []
    def visit_Assign(self, node: ast.Assign) -> Any:
        assert len(node.targets) == 1
        if isinstance(node.targets[0], ast.Tuple):
            for el in node.targets[0].elts:
                identifier = get_name(el)
                self.assignments.append(Assignment(node, identifier, len(self.assignments)))
        else:
            identifier = get_name(node.targets[0])
            self.assignments.append(Assignment(node, identifier, len(self.assignments)))
        self.generic_visit(node)

class FunctionDefinition:
    def __init__(self, node: ast.FunctionDef):
        self.node = node
        self.name = node.name

def _get_id_str(identifier: ast.AST):
        assert isinstance(identifier, (ast.Name, ast.arg, ast.FunctionDef)), f"Identifier has wrong type {ast.dump(identifier)}"
        if isinstance(identifier, ast.Name):
            return identifier.id
        # if isinstance(identifier, ast.Attribute):
        #     return identifier.attr
        if isinstance(identifier, ast.arg):
            return identifier.arg
        if isinstance(identifier, ast.FunctionDef):
            return identifier.name
        
def _identifieres_are_the_same(scope_info, identifier1: ast.AST, identifier2: ast.AST):
    if isinstance(identifier1, ast.Attribute) or isinstance(identifier2, ast.Attribute):
        # module function calls have call.func attribute which has no scope (is not user-defined symbol)
        # e.g. np.array
        return False
    
    id1 = _get_id_str(identifier1)
    id2 = _get_id_str(identifier2)
    scope1 = scope_info[identifier1]
    scope2 = scope_info[identifier2]
    # Function args have scope of corresponding function
    # FunctionDefs have scope in which the function is defined
    # e.g. if function is defined in global scope a corresponding function call has call.func name with global scope

    return id1 == id2 and scope1 == scope2

class ScopedTree:
    def __init__(self, syntax_tree: SyntaxTree, scope_info, all_definitions, all_functions, all_user_symbols, cfgs, is_container_variable):
        self.syntax_tree = syntax_tree
        self.root_node = syntax_tree.root_node
        self.scope_info = scope_info
        self.all_definitions = all_definitions
        self.all_functions = all_functions
        # print("all_functions:", [f.name for f in self.all_functions])
        self.all_user_symbols = all_user_symbols
        self.cfgs = cfgs
        self.is_container_variable = is_container_variable

    def get_node_for_id(self, id: str) -> ast.AST:
        return self.syntax_tree.id_to_node[id]
    
    def get_id_for_node(self, node: ast.AST) -> str:
        return self.syntax_tree.node_to_id[node]
    
        
    def identifieres_are_the_same(self, identifier1: ast.AST, identifier2: ast.AST):
        return _identifieres_are_the_same(self.scope_info, identifier1, identifier2)
        
    def get_cfgnode_for_syntaxnode(self, node: ast.AST):
        for _, cfg in self.cfgs.items():
            for cfgnode in cfg.nodes:
                if isinstance(cfgnode, (AssignNode, BranchNode, ReturnNode, ExprNode, LoopIterNode)) and is_descendant(cfgnode.syntaxnode, node):
                    return cfg, cfgnode
        raise Exception(f"No CFGNode found for syntaxnode {ast.dump(node)}")
    
    def get_cfg_for_function_syntaxnode(self, node: ast.FunctionDef):
        if node not in self.cfgs:
            raise Exception(f"No CFGNode found for function {node}")
        return self.cfgs[node]


def NameFinder():
    return NodeFinder(
        lambda node: isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load),
        lambda node: node)

def is_referenced_identifier(identifier: ast.Name):
    return isinstance(identifier, ast.Name) and isinstance(identifier.parent, ast.Subscript)

def get_scoped_tree(syntax_tree: SyntaxTree):
    node = syntax_tree.root_node
    scope_info = ast_scope.annotate(node) # ast.Name + ast.FunctionDef -> Scope
    visitor = AssignmentCollector()
    visitor.visit(node)
    all_definitions = visitor.assignments
    all_functions = [FunctionDefinition(f) for f in get_user_defined_functions(node)]
    all_user_symbols = {definition.name for definition in all_definitions}
    for f in all_functions:
        all_user_symbols.add(f.name)
        for arg in f.node.args.args:
            all_user_symbols.add(arg.arg) # add parameter name of function

    
    cfgs = get_cfg_representation(node, syntax_tree.node_to_id)

    all_identifiers = NameFinder().visit(node)
    referenced_identifiers = set(identifier for identifier in all_identifiers if is_referenced_identifier(identifier))
    is_container_variable = dict()
    for identifier in all_identifiers:
        # check if identifier x is somewhere used as x[...]
        is_container_variable[identifier] = any(
            _identifieres_are_the_same(scope_info, identifier, ref_identifier)
            for ref_identifier in referenced_identifiers
        )
    # print(sorted(list({(name.id, b) for name,b in is_container_variable.items()})))


    return ScopedTree(syntax_tree, scope_info, all_definitions, all_functions, all_user_symbols, cfgs, is_container_variable)
