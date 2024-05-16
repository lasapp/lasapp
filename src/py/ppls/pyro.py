from .ppl import PPL, VariableDefinition
import ast
from ast_utils.utils import get_call_name
from .torch_distributions import parse_torch_distribution
from ast_utils.preprocess import SyntaxTree
from .pyro_pymc_preproc import PyroPyMCPreprocessor

class Pyro(PPL):
    def __init__(self) -> None:
        super().__init__()

    def is_random_variable_definition(self, node: ast.AST) -> bool:
        match node:
            case ast.Assign(value=ast.Call(func=ast.Attribute(value=ast.Name(id=_id), attr=_attr))) if _id == "pyro" and _attr == "sample":
                return True
            case ast.Assign(value=ast.Call(func=ast.Name(id=_id))) if _id == "sample":
                return True
        return False
    
    def get_random_variable_name(self, variable: VariableDefinition) -> str:
        assert isinstance(variable.node, ast.Assign)
        call_node = variable.node.value
        return ast.unparse(call_node.args[0])
    
    def get_address_node(self, variable: VariableDefinition) -> ast.AST:
        assert isinstance(variable.node, ast.Assign)
        call_node = variable.node.value
        return call_node.args[0]

    def is_model(self, node: ast.AST) -> bool:
        return isinstance(node, ast.FunctionDef)
    
    def get_model_name(self, node) -> bool:
        return node.name
    
    def is_observed(self, variable: VariableDefinition) -> bool:
        assert isinstance(variable.node, ast.Assign)
        call_node = variable.node.value
        for kw in call_node.keywords:
            if kw.arg == 'obs':
                return True
        return False
    
    def get_distribution_node(self, variable: VariableDefinition) -> ast.AST:
        assert isinstance(variable.node, ast.Assign)
        call_node = variable.node.value
        dist_node = call_node.args[1]

        return dist_node

    
    def get_distribution(self, distribution_node: ast.AST) -> tuple[str, dict[str, ast.AST]]:
        if not isinstance(distribution_node, ast.Call):
            return "Unknown", {"distribution": distribution_node}
        
        # dist.Normal(0,1).to_event() ... -> dist.Normal(0,1)
        while isinstance(distribution_node, ast.Call) and isinstance(distribution_node.func, ast.Attribute) and isinstance(distribution_node.func.value, ast.Call):
            distribution_node = distribution_node.func.value

        name = get_call_name(distribution_node)

        args = distribution_node.args
        kwargs = {kw.arg: kw.value for kw in distribution_node.keywords}

        dist_name, dist_params = parse_torch_distribution(name, args, kwargs)

        return dist_name, dist_params
    
    def is_rogue_rv_node(self, node: ast.Call) -> bool:
        match node:
            case ast.Call(func=ast.Attribute(value=ast.Name(id=_id), attr=_attr)) if _id == "pyro" and _attr == "sample":
                return True
            case ast.Call(func=ast.Name(id=_id)) if _id == "sample":
                return True
        return False
    
    def preprocess_syntax_tree(self, syntax_tree: SyntaxTree) -> SyntaxTree:
        PyroPyMCPreprocessor(syntax_tree, lambda node: self.is_rogue_rv_node(node)).visit(syntax_tree.root_node)
        # print(ast.dump(syntax_tree.root_node, indent=1))
        # print(ast.unparse(syntax_tree.root_node))
        return syntax_tree