import ast
from typing import Union
from ast_utils.preprocess import SyntaxTree

class VariableDefinition:
    def __init__(self, node: ast.AST):
        self.node = node

class Model:
    def __init__(self, name: str, node: ast.AST):
        self.name = name
        self.node = node

class PPL:
    def __init__(self) -> None:
        pass

    def is_random_variable_definition(self, node: ast.AST) -> bool:
        raise NotImplementedError
    
    def is_model(self, node: ast.AST) -> bool:
        raise NotImplementedError
    
    def get_model_name(self, node: ast.AST) -> str:
        raise NotImplementedError
    
    def get_random_variable_name(self, variable: VariableDefinition) -> str:
        raise NotImplementedError
    
    def get_address_node(self, variable: VariableDefinition) -> ast.AST:
        raise NotImplementedError
    
    def is_observed(self, variable: VariableDefinition) -> bool:
        raise NotImplementedError
    
    def get_distribution_node(self, variable: VariableDefinition) -> ast.AST:
        raise NotImplementedError
    
    def get_distribution(self, distribution_node: ast.AST) -> tuple[str, dict[str, ast.AST]]:
        raise NotImplementedError
    
    def get_program_variable_name(self, variable: VariableDefinition) -> Union[str,None]:
        raise NotImplementedError

    def preprocess_syntax_tree(self, syntax_tree: SyntaxTree) -> SyntaxTree:
        raise NotImplementedError