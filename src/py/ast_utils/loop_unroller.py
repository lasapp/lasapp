import ast
from .utils import Block
from copy import deepcopy

class NameReplacer(ast.NodeTransformer):
    def __init__(self, id, replace_with):
        self.id = id
        self.replace_with = replace_with
    def visit_Name(self, node: ast.Name):
        if node.id == self.id:
            return deepcopy(self.replace_with)
        return self.generic_visit(node)
    
# call after BlockTransformer, before PositionParentAdder
class LoopUnroller(ast.NodeTransformer):
    def __init__(self, N) -> None:
        self.N = N

    def visit_Block(self, node: Block):
        # print("LoopUnroller Block", node)
        new_block_body = []
        for stmt in node:
            match stmt:
                case ast.For(target=ast.Name(), iter=ast.Call(func=ast.Name(id=_func_id), args=_args)) if _func_id == 'range':
                    # print("LoopUnroller For:", ast.dump(stmt.target), ast.dump(stmt.iter))
                    iter_range = range(self.N)
                    match _args:
                        case [ast.Constant(value=value)]:
                            iter_range = range(value)
                        case [ast.Constant(value=value1), ast.Constant(value=value2)]:
                            iter_range = range(value1, value2)
                    for i in iter_range:
                        unrolled_for_body = deepcopy(stmt.body)
                        NameReplacer(stmt.target.id, ast.Constant(value=i)).visit(unrolled_for_body)
                        new_block_body.append(unrolled_for_body)
                case _:
                    new_block_body.append(stmt)

        new_block = Block(new_block_body)

        # print(node)
        return self.generic_visit(new_block)
    

# s = """
# x = [0,1,2]
# for i in range(3):
#     x[i] = x[i] + i
# """
# s = """
# x = something()
# for i in range(3):
#     for j in range(2):
#         x[i, j] = x[i] + j
# """
# syntax_tree = ast.parse(s)
# BlockNodeTransformer().visit(syntax_tree)
# print(ast.unparse(syntax_tree))
# LoopUnroller(4).visit(syntax_tree)
# print(ast.unparse(syntax_tree))

# for item in syntax_tree.body:
#     print(item)

# c = ast.parse("1").body[0]
# b = Block([c,c])
# print(list(b))
# print(list(deepcopy(b)))
# b2 = Block([b,b])
# print(list(b2))
# print(list(deepcopy(b2)))
# print(id(b2))

# class _Unparser(ast._Unparser):
#     def __init__(self):
#         super().__init__()
#         self.i = 0
#     def visit_Block(self, node: Block):
#         for item in node:
#             self.traverse(item)

# def unparse(ast_obj):
#     unparser = _Unparser()
#     return unparser.visit(ast_obj)

