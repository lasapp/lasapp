import ast
from typing import Any
from ast_utils.node_finder import NodeFinder
from ast_utils.node_finders import get_user_defined_functions
from ast_utils.utils import get_call_name

class CallFinder(ast.NodeVisitor):
    def __init__(self) -> None:
        self.calls = []
    def visit_Call(self, node: ast.Call) -> Any:
        self.calls.append(node)
        self.generic_visit(node)
    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        # don't visit nested functions
        pass

def get_called_functions(functions, scope_info, node: ast.AST):
    call_finder = CallFinder()
    if isinstance(node, ast.FunctionDef):
        call_finder.visit(node.body)
    else:
        call_finder.visit(node)

    
    # get function definitions for all calls
    called_functions = []
    for call in call_finder.calls:
        call_name = get_call_name(call)
        for function in functions:
            # same name and scope
            if call_name == function.name and scope_info[call.func] == scope_info[function]:
                called_functions.append(function)
                break

    return called_functions

class CallGraphAnalyzer(ast.NodeVisitor):
    def __init__(self, functions, scope_info):
        self.functions = functions
        self.scope_info = scope_info
        self.call_graph = {}

    def visit_FunctionDef(self, node: ast.FunctionDef):
        
        self.call_graph[node] = get_called_functions(self.functions, self.scope_info, node)
        
        self.generic_visit(node)

        
    
def compute_call_graph(syntax_tree: ast.AST, scope_info, node: ast.AST):
    functions = get_user_defined_functions(syntax_tree)
    
    cga = CallGraphAnalyzer(functions, scope_info)
    cga.visit(syntax_tree) # for the entire syntax_tree (file)


    if node is not None:
        # get subset called by node
        call_subgraph = {}

        called_functions = get_called_functions(functions, scope_info, node)
        call_subgraph[node] = called_functions.copy()
        
        # traverse complete call graph starting from node to get only functions that are reachable from node
        processed = set()
        to_process = called_functions
        while len(to_process) > 0:
            called = to_process.pop()
            call_subgraph[called] = cga.call_graph[called]
            processed.add(called)

            for sub_call in cga.call_graph[called]:
                if sub_call not in processed and sub_call not in to_process:
                    to_process.append(sub_call)

        return call_subgraph
    else:
        # return complete call graph
        return cga.call_graph
        