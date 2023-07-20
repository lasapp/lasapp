from .ppl import PPL, VariableDefinition
import ast
from ast_utils.utils import get_call_name, source_text
from ast_utils.node_finder import NodeFinder
from .torch_distributions import parse_torch_distribution
from typing import Union

class Beanmachine(PPL):
    def __init__(self) -> None:
        super().__init__()

    def is_random_variable_definition(self, node: ast.AST) -> bool:
        if not isinstance(node, ast.FunctionDef):    
            return False
        if len(node.decorator_list) == 0:
            return False
        
        decorator = node.decorator_list[0]
        if isinstance(decorator, ast.Name) and node.func.id == 'random_variable':
            return True
        elif isinstance(decorator, ast.Attribute) and isinstance(decorator.value, ast.Name):
            return decorator.value.id == 'bm' and decorator.attr in ('functional', 'random_variable') # TODO: check how beanmachine is imported
        else:
            return False
        
    def get_random_variable_name(self, variable: VariableDefinition) -> str:
        s = source_text(variable.node)
        return s.partition("def ")[2].partition(":")[0]
    
    def get_program_variable_name(self, variable: VariableDefinition) -> str:
        return variable.node.name

    def is_model(self, node: ast.AST) -> bool:
        return isinstance(node, ast.Module)
    
    def get_model_name(self, node: ast.AST) -> str:
        return "model"# node.name
    
    # def is_model(self, node) -> bool:
    #     if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
    #         return True
    #     return False
    
    # def get_model_name(self, node) -> bool:
    #     return node.targets[0].id

    def is_obervation_assignment(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Assign):
            if (isinstance(node.targets[0], ast.Subscript) and
                    isinstance(node.targets[0].value, ast.Name) and
                    node.targets[0].value.id == "observations"
                    ):
                    # observations[variable(...)] = value
                    key = node.targets[0].slice
                    # should be call
                    if isinstance(key, ast.Call):
                        current = node
                        # only topscope assignments
                        while current.parent is not None:
                            current = current.parent
                            if isinstance(current, ast.FunctionDef):
                                return False
                        return True
        return False
        
    def is_observed(self, variable: VariableDefinition) -> bool:
        # search for observation dict in toplevel
        rootnode = variable.node
        while rootnode.parent is not None:
            rootnode = rootnode.parent
        
        if not isinstance(rootnode, ast.Module):
            return False
        
        variable_name = variable.node.name # name of function
        
        for stmt in rootnode.body:
            if isinstance(stmt, ast.Assign):
                if (isinstance(stmt.targets[0], ast.Name) and
                    stmt.targets[0].id == "observations" and
                    isinstance(stmt.value, ast.Dict)
                    ):
                    # observations = {variable(...): value}
                    # only compare call name to function definition, not arguments
                    for key in stmt.value.keys:
                        # should all be calls
                        if isinstance(key, ast.Call):
                            key_call_name = get_call_name(key)
                            if key_call_name == variable_name:
                                return True
                

        # get all topscope observations[variable(...)] = value
        stmts = NodeFinder(self.is_obervation_assignment, lambda x: x).visit(rootnode)
        for stmt in stmts:
            key = stmt.targets[0].slice
            key_call_name = get_call_name(key)
            if key_call_name == variable_name:
                return True

        return False
    
    def get_distribution_node(self, variable: VariableDefinition) -> ast.AST:
        body = variable.node.body

        return_finder = NodeFinder(
            lambda x: isinstance(x, ast.Return),
            lambda x: x
        )
        # find all return statements
        return_stmts = return_finder.visit(body)
        if len(return_stmts) == 1:
            # if we have one return statement, we take return expression
            return return_stmts[0].value
        else:
            # we take function body
            return body
        
    
    def get_distribution(self, distribution_node: ast.AST) -> tuple[str, dict[str, ast.AST]]:
        # same as pyro (torch)

        if not isinstance(distribution_node, ast.Call):
            return "Unknown", {"distribution": distribution_node}
        
        name = get_call_name(distribution_node)
        dist_name = name

        args = distribution_node.args
        kwargs = {kw.arg: kw.value for kw in distribution_node.keywords}

        dist_name, dist_params = parse_torch_distribution(name, args, kwargs)

        return dist_name, dist_params