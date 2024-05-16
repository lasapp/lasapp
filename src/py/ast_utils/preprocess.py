
import ast
import ast_scope
from .utils import Block, IdPrinter
from .multitarget_assignments import MultitargetTransformer
from .call_uniquifier import CallUniquifier
from .loop_unroller import LoopUnroller

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
    def __getitem__(self, i):
        return self.file_content[i]

# The bodies of modules, functions, branches, for, and while loops are lists
# we wrap them in Block struct
class BlockNodeTransformer(ast.NodeVisitor):
    def to_block(self, body):
        if len(body) >= 1:
            return Block(body)
        else:
            raise ValueError("Tried to create Block from empty body.")
    
    def visit_Module(self, node: ast.Module):
        node.body = self.to_block(node.body)
        return self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        node.body = self.to_block(node.body)    
        return self.generic_visit(node)
        
    def visit_If(self, node: ast.If):
        node.body = self.to_block(node.body)
        if len(node.orelse) == 0:
            # node.orelse = None
            delattr(node, "orelse")
            node._fields = tuple(field for field in node._fields if field != "orelse")
        else:
            node.orelse = self.to_block(node.orelse)    
        return self.generic_visit(node)

    def visit_For(self, node: ast.For):
        node.body = self.to_block(node.body)
        return self.generic_visit(node)

    def visit_While(self, node: ast.While):
        node.body = self.to_block(node.body)
        return self.generic_visit(node)

    def visit_With(self, node: ast.With):
        node.body = self.to_block(node.body)
        return self.generic_visit(node)

# Add position information to nodes and their parent
class PositionParentAdder(ast.NodeVisitor):
    def __init__(self, file_content: str, line_offsets: list[int]):
        super().__init__()
        self.file_content = FileContent(file_content)
        self.line_offsets = line_offsets

    def visit(self, node: ast.AST):

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
        elif isinstance(node, ast.arguments):
            # add position to arguments
            func_def = node.parent
            start, end = get_first_last_byte(func_def, self.line_offsets)

            while self.file_content[start] != '(' and start < end:
                start += 1
            start += 1

            new_end = start
            while self.file_content[new_end] != ')' and new_end < end:
                new_end += 1
            new_end -= 1
            end = new_end

            node.position = start
            node.end_position = end
            node.span = node.end_position - node.position
            node.source = self.file_content
            
        for child in ast.iter_child_nodes(node):
            child.parent = node
        
        self.generic_visit(node)

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


# Confusion (1)
# if we want to deepcopy a syntaxnode we have to make sure that two syntaxtree instances
# do not share any object. ast.Store and ast.Load are singletons however
# I am still not too sure about this
# There are also other singleton classes (like ast.Add)
# I do not understand when deepcopying works properly
# class Unsingletonifier(ast.NodeTransformer):
#     def visit_Store(self, node: ast.Store):
#         return ast.Store()
#     def visit_Load(self, node: ast.Load):
#         return ast.Load()
#     def visit_Del(self, node: ast.Del):
#         return ast.Del()

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

    def add_node(self, node: ast.AST):
        i = f"node_{len(self.node_to_id) + 1}"
        self.node_to_id[node] = i
        self.id_to_node[i] = node

from copy import deepcopy
def preprocess_syntaxtree(syntax_tree: ast.AST, file_content: str, line_offsets: list[int],
                          n_unroll_loops: int, uniquify_calls: bool = True) -> SyntaxTree:
    
    syntax_tree = deepcopy(syntax_tree) # this is a hack to deal with (1), unsingletonifies everything
    MultitargetTransformer().visit(syntax_tree)
    if uniquify_calls:
        prelim_scope_info = ast_scope.annotate(syntax_tree)
        CallUniquifier(syntax_tree, prelim_scope_info).visit(syntax_tree)
    BlockNodeTransformer().visit(syntax_tree)
    if n_unroll_loops > 0:
        print("Unroll Loops")
        LoopUnroller(n_unroll_loops).visit(syntax_tree)
    syntax_tree.parent = None
    PositionParentAdder(file_content, line_offsets).visit(syntax_tree)
    # print(ast.unparse(syntax_tree))
    return SyntaxTree(syntax_tree)
