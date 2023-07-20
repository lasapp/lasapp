from .ppl import PPL, VariableDefinition
import ast
from ast_utils.utils import get_call_name, get_name
from .torch_distributions import parse_torch_distribution

class Pyro(PPL):
    def __init__(self) -> None:
        super().__init__()

    def is_random_variable_definition(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Assign):
           return self.is_random_variable_definition(node.value)

        if not isinstance(node, ast.Call):
            return False
        
        if isinstance(node.func, ast.Name) and node.func.id == 'sample':
            return True
        elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            return node.func.value.id == 'pyro' and node.func.attr == 'sample' # TODO: check how pyro is imported
        else:
            return False
        
    def get_random_variable_name(self, variable: VariableDefinition) -> str:
        call_node = variable.node.value if isinstance(variable.node, ast.Assign) else variable.node
        return ast.unparse(call_node.args[0])

    def get_program_variable_name(self, variable: VariableDefinition) -> str:
        if isinstance(variable.node, ast.Assign):
            return get_name(variable.node.targets[0]).id
        else:
            return None
        
    def is_model(self, node: ast.AST) -> bool:
        return isinstance(node, ast.FunctionDef)
    
    def get_model_name(self, node) -> bool:
        return node.name
    
    def is_observed(self, variable: VariableDefinition) -> bool:
        call_node = variable.node.value if isinstance(variable.node, ast.Assign) else variable.node
        for kw in call_node.keywords:
            if kw.arg == 'obs':
                return True
        return False
    
    def get_distribution_node(self, variable: VariableDefinition) -> ast.AST:
        call_node = variable.node.value if isinstance(variable.node, ast.Assign) else variable.node
        return call_node.args[1]

    
    def get_distribution(self, distribution_node: ast.AST) -> tuple[str, dict[str, ast.AST]]:
        if not isinstance(distribution_node, ast.Call):
            return "Unknown", {"distribution": distribution_node}
        
        name = get_call_name(distribution_node)

        args = distribution_node.args
        kwargs = {kw.arg: kw.value for kw in distribution_node.keywords}

        dist_name, dist_params = parse_torch_distribution(name, args, kwargs)

        return dist_name, dist_params