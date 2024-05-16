import ast
import ast_scope
from copy import deepcopy
from ast_utils.node_finder import NodeFinder

# def foo(x):
#     return x
# foo(y)
# foo(z)
# ->
# def foo(x):
#     return x
# def foo1(x):
#     return x
# def foo2(x):
#     return x
# foo1(y)
# foo2(z)
# important to not overapproximate data deps of FuncArgNode

# TODO:
# check if we need to do this recursively (calls of user-def functions in body of user-def functions)

def CallFinder(func_syntaxnode: ast.FunctionDef, call_unquifier):
    assert isinstance(func_syntaxnode, ast.FunctionDef)
    if func_syntaxnode not in call_unquifier.scope_info:
        # if we deepcopy a function foo which defines a nested function,
        # we have to find scope for the nested function (deepcopied foo)
        call_unquifier.scope_info = ast_scope.annotate(call_unquifier.root_node)

    scope_info = call_unquifier.scope_info
    return NodeFinder(
        lambda node: (isinstance(node, ast.Call) and
                      isinstance(node.func, ast.Name) and
                      node.func.id == func_syntaxnode.name and
                      node.func in scope_info and
                      scope_info[node.func] == scope_info[func_syntaxnode]),
        lambda node: node
    )

class CallUniquifier(ast.NodeVisitor):
    def __init__(self, root_node, scope_info) -> None:
        self.root_node = root_node
        self.scope_info = scope_info
        # scope_info must be updated after transforming ast

    def visit(self, node: ast.AST):
        if hasattr(node, "body") and isinstance(node.body, list):
            new_body = []
            for stmt in node.body:
                new_body.append(stmt)
                match stmt:
                    case ast.FunctionDef(name=_name):
                        call_finder = CallFinder(stmt, self)
                        calls = call_finder.visit(self.root_node)
                        if len(calls) > 1:
                            for i, call in enumerate(calls):
                                new_name = f"{_name}_{i}"
                                call.func.id = new_name
                                new_func = deepcopy(stmt)
                                new_func.name = new_name
                                new_body.append(new_func)
            node.body = new_body

        return self.generic_visit(node)
