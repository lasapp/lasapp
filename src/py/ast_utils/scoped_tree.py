import ast
from typing import Any
import ast_scope
from ast_utils.node_finder import NodeFinder
from ast_utils.node_finders import get_user_defined_functions
from ast_utils.position_parent import SyntaxTree
from ast_utils.utils import get_name

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

class ScopedTree:
    def __init__(self, syntax_tree: SyntaxTree, scope_info, all_definitions, all_functions, all_user_symbols):
        self.syntax_tree = syntax_tree
        self.root_node = syntax_tree.root_node
        self.scope_info = scope_info
        self.all_definitions = all_definitions
        self.all_functions = all_functions
        # print("all_functions:", [f.name for f in self.all_functions])
        self.all_user_symbols = all_user_symbols

    def get_node_for_id(self, id: str) -> ast.AST:
        return self.syntax_tree.id_to_node[id]
    
    def get_id_for_node(self, node: ast.AST) -> str:
        return self.syntax_tree.node_to_id[node]

def get_scoped_tree(syntax_tree: SyntaxTree):
    node = syntax_tree.root_node
    scope_info = ast_scope.annotate(node) # ast.Name + ast.FunctionDef -> Scope
    visitor = AssignmentCollector()
    visitor.visit(node)
    all_definitions = visitor.assignments
    all_functions = [FunctionDefinition(f) for f in get_user_defined_functions(node)]
    all_user_symbols = {definition.name for definition in all_definitions} | {f.name for f in all_functions}
    return ScopedTree(syntax_tree, scope_info, all_definitions, all_functions, all_user_symbols)
