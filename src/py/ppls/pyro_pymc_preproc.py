from typing import Callable
import ast
from ast_utils.preprocess import SyntaxTree
from ast_utils.utils import Block

def get_pos_args(stmt):
    return {
        "lineno": stmt.lineno,
        "col_offset": stmt.col_offset,
        "end_lineno": stmt.end_lineno,
        "end_col_offset": stmt.end_col_offset,
        "position": stmt.position,
        "end_position": stmt.end_position,
        "span": stmt.span,
        "source": stmt.source,
    }


# replaces rogue pm.Dist(...) | pyro.sample(...) nodes with proper assignments x = pm.Dist(...), x = pyro.sample(...)
class PyroPyMCPreprocessor(ast.NodeTransformer):
        def __init__(self, syntax_tree: SyntaxTree, is_rogue_rv_node: Callable[[ast.Call], bool] ) -> None:
            self.syntax_tree = syntax_tree
            self.is_rogue_rv_node = is_rogue_rv_node
            self.block_insertions = {}

        def visit_Call(self, node: ast.Call):
            node = self.generic_visit(node)
            if self.is_rogue_rv_node(node):
                # print("RV", ast.unparse(node), node.parent)
                if not isinstance(node.parent, ast.Assign):
                    if isinstance(node.parent, ast.Expr):
                        if isinstance(node.parent.parent, Block):
                            # Block(elts=[...,Expr(node),...])
                            # -> Block(elts=[...,__TMP__ = node,...])
                            block = node.parent.parent
                            name = ast.Name(id=f"__TMP__{self.syntax_tree.node_to_id[node]}", ctx=ast.Store())
                            assign = ast.Assign(targets=[name], value=node, **get_pos_args(node))
                            self.syntax_tree.add_node(name)
                            self.syntax_tree.add_node(assign)
                            node.parent = assign
                            name.parent = assign
                            assign.parent = block
                            return assign
                        else:
                            raise Exception(f"PyroPyMCPreprocessor: RV {ast.unparse(node)} is expr and not child of block.")
                    else:
                        # Block(elts=[...,f(node),...])
                        # -> Block(elts=[...,__TMP__ = node, f(__TMP__), ...])
                        block = node.parent
                        while not isinstance(block, Block):
                            block = block.parent

                        name = ast.Name(id=f"__TMP__{self.syntax_tree.node_to_id[node]}", ctx=ast.Store())
                        assign = ast.Assign(targets=[name], value=node, **get_pos_args(node))
                        name_load = ast.Name(id=name.id, ctx=ast.Load(), **get_pos_args(node))
                        self.syntax_tree.add_node(name)
                        self.syntax_tree.add_node(assign)
                        self.syntax_tree.add_node(name_load)
                        # we add assign node in parent block before stmt that contains node
                        self.block_insertions[block].append(assign)

                        name.parent = assign
                        assign.parent = block
                        name_load.parent = node.parent

                        return name_load
                    
            return node
        
        def visit_Block(self, node: Block):
            self.block_insertions[node] = []
            new_elts = []
            for stmt in node.elts:
                value = self.visit(stmt)
                assert value is not None
                if len(self.block_insertions[node]) > 0:
                    # visiting stmt generated some new stmts that should be assigned before it
                    new_elts.extend(self.block_insertions[node])
                    self.block_insertions[node] = []
                new_elts.append(value)
            node.elts = new_elts
            del self.block_insertions[node]
            return node

        def visit_Expr(self, node: ast.Expr):
            value = self.visit(node.value)
            if isinstance(value, ast.Assign):
                return value
            else:
                node.value = value
                return node