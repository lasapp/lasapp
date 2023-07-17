import ast
from typing import Union
def get_file_content(file_name: str):
    with open(file_name, encoding="utf-8") as f:
        file_content = f.read()
        return file_content
    
def get_line_offsets(file_name: str) -> list[int]:
    with open(file_name, encoding="utf-8") as f:
        line_offsets: list[int] = []
        cumsum = 0
        for line in f:
            line_offsets.append(cumsum)
            cumsum += len(line)
        
        line_offsets.append(cumsum)
        return line_offsets
    

def get_line_offsets_for_str(s: str) -> list[int]:
    line_offsets: list[int] = []
    cumsum = 0
    for line in s.splitlines(keepends=True):
        line_offsets.append(cumsum)
        cumsum += len(line)
    
    line_offsets.append(cumsum)
    return line_offsets
    

# ast.unparse does not correctly reproduce source text (removes whitespaces etc.)
def source_text(node):
    start, end = node.position, node.end_position
    return node.source.file_content[start:end]

# Returns the identifier of an assignment target.
# For indexed assignment, returns container identifier.
# TODO: maybe change to get_identifier
def get_name(target: ast.AST) -> ast.Name:
    if isinstance(target, ast.Name):
        return target
    if isinstance(target, ast.Subscript):
        assert isinstance(target.value, ast.Name)
        return target.value
    raise ValueError("Name not found.")

def get_assignment_name(node: ast.Assign) -> ast.Name:
    assert isinstance(node, ast.Assign) and len(node.targets) == 1
    return get_name(node.targets[0])

# For a call SyntaxNode, returns the Identifier SyntaxNode of the called function.
# If the function has module prefix, the prefix is omitted.
def get_call_name(node: ast.Call) -> str:
    assert isinstance(node, ast.Call)
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
        return node.func.attr


class Block(ast.AST):
    def __init__(self, body: list[ast.AST]):
        fields = []
        for i, stmt in enumerate(body):
            field = f"stmt_{i}"
            setattr(self, field, stmt)
            fields.append(field)
        self._fields = fields
        # take position from first element
        self.lineno = body[0].lineno
        self.col_offset = body[0].col_offset
        # take position from last element
        self.end_lineno = body[-1].end_lineno
        self.end_col_offset = body[-1].end_col_offset
        self._attributes = ("lineno", "col_offset", "end_lineno", "end_col_offset")

    def __len__(self):
        return len(self._fields)
    
    def __getitem__(self, key):
        return getattr(self, f"stmt_{key}")     
    
    def __iter__(self):
        return (self[i] for i in range(len(self)))
    
# Returns true if the two nodes are located in mutually exclusive if branches
# i.e. if node is in descendant of if branch and other of else branch, and vice versa
def is_in_different_branch(node: ast.AST, other: ast.AST) -> bool:
    current_parent = node.parent
    while current_parent is not None:
        # last check is redundant, but just to be safe, if I change BlockTransformer
        if isinstance(current_parent, ast.If) and hasattr(current_parent, "orelse") and current_parent.orelse is not None:
            branch_1 = current_parent.body
            branch_2 = current_parent.orelse
            if is_descendant(branch_1, node) and is_descendant(branch_2, other):
                return True
            if is_descendant(branch_1, other) and is_descendant(branch_2, node):
                return True
        current_parent = current_parent.parent
    return False


# We can check if one node is a descendant of another,
# by traversing up the parent
def is_descendant(parent: ast.AST, node: ast.AST) -> bool:
    if parent == node:
        return True
    while node.parent is not None:
        node = node.parent
        if parent == node:
            return True
    return False