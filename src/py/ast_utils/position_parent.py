
import ast
from typing import Any
from .utils import Block

# returns the indices of source text of node in utf8 source code
def get_first_last_byte(node: ast.AST, line_offsets: list[int]):
    start = line_offsets[node.lineno-1] + node.col_offset
    end = line_offsets[node.end_lineno-1] + node.end_col_offset
    return start, end

def get_range(node: ast.AST):
    return node.position, node.end_position

def has_position_info(node: ast.AST):
    return hasattr(node, "lineno") and hasattr(node, "col_offset") and hasattr(node, "end_lineno") and hasattr(node, "end_col_offset")

class FileContent:
    def __init__(self, file_content):
        self.file_content = file_content
    def __len__(self):
        return len(self.file_content)

# The bodies of functions, branches, for, and while loops are lists
# we wrap them in Block struct
class BlockNodeTransformer(ast.NodeVisitor):
    def to_block(self, body):
        if len(body) >= 1:
            return Block(body)
        else:
            raise ValueError("Tried to create Block from empty body.")
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        node.body = self.to_block(node.body)    
        self.generic_visit(node)
        
    def visit_If(self, node: ast.If):
        node.body = self.to_block(node.body)
        if len(node.orelse) == 0:
            # node.orelse = None
            delattr(node, "orelse")
            node._fields = tuple(field for field in node._fields if field != "orelse")
        else:
            node.orelse = self.to_block(node.orelse)    
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        node.body = self.to_block(node.body)
        self.generic_visit(node)

    def visit_While(self, node: ast.While):
        node.body = self.to_block(node.body)
        self.generic_visit(node)

# Add position information to nodes and their parent
class PositionParentAdder(ast.NodeVisitor):
    def __init__(self, file_content: str, line_offsets: list[int]):
        super().__init__()
        self.file_content = FileContent(file_content)
        self.line_offsets = line_offsets

    def visit(self, node: ast.AST):
        self.generic_visit(node)

        if has_position_info(node):
            start, end = get_first_last_byte(node, self.line_offsets)
            node.position = start
            node.end_position = end
            node.span = node.end_position - node.position
            node.source = self.file_content
        elif isinstance(node, ast.Module):
            node.position = 0
            node.end_position = len(self.file_content)
            node.span = node.end_position - node.position
            node.source = self.file_content


        for child in ast.iter_child_nodes(node):
            child.parent = node

        # min_child_position = float("inf")
        # max_child_end_position = -float("inf")

        # for child in ast.iter_child_nodes(node):
        #     min_child_position = min(min_child_position, child.min_child_position)
        #     max_child_end_position = max(max_child_end_position, child.max_child_end_position)
        #     child.parent = node

        # node.source = self.file_content
        # node.min_child_position = min_child_position
        # node.max_child_end_position = max_child_end_position

        # if not has_position_info(node):
        #     node.position = min_child_position
        #     node.end_position = max_child_end_position
        #     node.span = node.end_position - node.position


class NodeIdAssigner(ast.NodeVisitor):
    def __init__(self) -> None:
        self.node_to_id = {}
        self.id_to_node = {}

    def visit(self, node: ast.AST):
        i = f"node_{len(self.node_to_id) + 1}"
        self.node_to_id[node] = i
        self.id_to_node[i] = node

        self.generic_visit(node)

class SyntaxTree:
    def __init__(self, root_node: ast.AST) -> None:
        self.root_node = root_node

        node_id_assigner = NodeIdAssigner()
        node_id_assigner.visit(self.root_node)
        self.node_to_id = node_id_assigner.node_to_id
        self.id_to_node = node_id_assigner.id_to_node

def add_position_and_parent(syntax_tree: ast.AST, file_content: str, line_offsets: list[int]) -> SyntaxTree:
    BlockNodeTransformer().visit(syntax_tree)
    syntax_tree.parent = None
    PositionParentAdder(file_content, line_offsets).visit(syntax_tree)
    return SyntaxTree(syntax_tree)

# Nodes can be uniquely identified by their range in the UTF8 source code.
# This function returns the node of a tree for a given range.
# syntax_tree has to be transformend with add_position_and_parent first
# does not work, because not every node has position info
# def get_subnode_for_range(syntax_tree: ast.AST , start: int, end: int):
#     node = syntax_tree
#     if has_position_info(node):
#         if node.position == start and node.end_position == end:
#             return node
    
#     for child in ast.iter_child_nodes(node):
#         if has_position_info(child):
#             if child.position <= start and end <= child.end_position:
#                 return get_subnode_for_range(child, start, end)
            
#     raise Exception(f"Node for range {start}:{end} not found.")
 