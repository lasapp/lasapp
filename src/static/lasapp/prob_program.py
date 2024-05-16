import os

from .server_interface import *
from .jsonrpc_client import get_jsonrpc_client


class ProbabilisticProgram:
    def __init__(self, file_name: str, n_unroll_loops: int = 0, ppl=None) -> None:
        _, ext = os.path.splitext(file_name)
        if ext == '.py':
            socket_name = "./.pipe/python_rpc_socket"
        elif ext == '.jl':
            socket_name = "./.pipe/julia_rpc_socket"
        else:
            raise ValueError(f"Unknown file extension: {ext}")
        
        with open(file_name, encoding="utf-8") as f:
            file_content = f.read()
            
        if ppl is None:
            if 'pyro' in file_content:
                ppl = 'pyro'
            elif 'pymc' in file_content:
                ppl = 'pymc'
            elif 'Turing' in file_content:
                ppl = 'turing'
            elif 'beanmachine' in file_content:
                ppl = 'beanmachine'
            elif 'Gen' in file_content:
                ppl = 'gen'
            else:
                raise ValueError("No probabilistic framework found.")

        self.client = get_jsonrpc_client(socket_name)
        self.file_name = file_name
        self.ppl = ppl


        response = self.client.build_ast(file_name=file_name, ppl=ppl, n_unroll_loops=n_unroll_loops)
        tree_id = response["result"]
        self.tree_id = tree_id

    def close(self):
        self.client.close()

    def get_model(self) -> Model:
        return self.client.get_model(
            tree_id=self.tree_id, object_hook=Model.from_dict
        )
    
    def get_guide(self) -> Model:
        return self.client.get_guide(
            tree_id=self.tree_id, object_hook=Model.from_dict
        )

    def get_random_variables(self) -> list[RandomVariable]:
        return self.client.get_random_variables(
            tree_id=self.tree_id, object_hook=RandomVariable.from_dict
        )
        
    def get_data_dependencies(self, node: SyntaxNode) -> list[SyntaxNode]:
        return self.client.get_data_dependencies(
            node=node, tree_id=self.tree_id, object_hook=SyntaxNode.from_dict
        )

    def get_control_dependencies(self, node: SyntaxNode) -> list[ControlDependency]:
        return self.client.get_control_dependencies(
            node=node, tree_id=self.tree_id, object_hook=ControlDependency.from_dict
        )
    
    def estimate_value_range(self, expr: SyntaxNode, mask: dict[SyntaxNode,Interval]) -> Interval: 
        mask = list(mask.items())
        return self.client.estimate_value_range(
            expr=expr,
            tree_id=self.tree_id,
            mask=mask,
            object_hook=Interval.from_dict
        )
    
    def get_call_graph(self, node: SyntaxNode) -> list[CallGraphNode]:
        return self.client.get_call_graph(
            tree_id=self.tree_id,
            node=node,
            object_hook=CallGraphNode.from_dict
        )
    
    def get_path_condition(self, node: SyntaxNode, root: SyntaxNode, mask: dict[SyntaxNode, SymbolicExpression]) -> SymbolicExpression:
        mask = list(mask.items())
        return self.client.get_path_conditions(
            tree_id=self.tree_id,
            root=root,
            nodes=[node],
            mask=mask,
            object_hook=SymbolicExpression.from_dict
        )[0]
    
    # batched version of get_path_condition
    def get_path_conditions(self, nodes: list[SyntaxNode], root: SyntaxNode, mask: dict[SyntaxNode, SymbolicExpression]) -> list[SymbolicExpression]:
        mask = list(mask.items())
        return self.client.get_path_conditions(
            tree_id=self.tree_id,
            root=root,
            nodes=nodes,
            mask=mask,
            object_hook=SymbolicExpression.from_dict
        )