import ast
from copy import deepcopy
import uuid

# x = y = 1 -> [x = 1, y = 1]
# x, y = value -> [tmp = value, x = tmp[0], y = tmp[1]]
# Called before BlockNodeTransformer
class MultitargetTransformer(ast.NodeVisitor):
    def visit(self, node: ast.AST):
        if hasattr(node, "body") and isinstance(node.body, list):
            new_body = []
            for stmt in node.body:
                position_args = {"lineno": stmt.lineno, "col_offset": stmt.col_offset, "end_lineno": stmt.end_lineno, "end_col_offset": stmt.end_col_offset}
                match stmt:
                    case ast.Assign(targets=[_, _, *_]): # x = y = 1
                        for name in stmt.targets:
                            new_stmt = deepcopy(stmt)
                            new_stmt.targets = [deepcopy(name)]
                            # new_stmt = ast.Assign(targets=[name], value=deepcopy(stmt.value), **position_args)
                            new_body.append(new_stmt)
                    case ast.Assign(targets=[ast.Tuple()], value=value): # x, y = 1
                        uuid4 = str(uuid.uuid4())[:5]
                        tmp_name_store = ast.Name(id=f'__TMP__{uuid4}', ctx=ast.Store())
                        tmp_name_load = ast.Name(id=tmp_name_store.id, ctx=ast.Load())
                        assign = ast.Assign(targets=[tmp_name_store], value=value, lineno=stmt.lineno, col_offset=stmt.col_offset, end_lineno=stmt.end_lineno, end_col_offset=stmt.col_offset)
                        new_body.append(assign)
                        tuple_target = stmt.targets[0]
                        for i, name in enumerate(tuple_target.elts):
                            assign = ast.Assign(targets=[name], value=ast.Subscript(value=tmp_name_load, slice=ast.Constant(value=i), ctx=ast.Load()), **position_args)
                            new_body.append(assign)

                    case _:
                        new_body.append(stmt)
                        # print(ast.unparse(stmt))
            node.body = new_body

        match node:
            case ast.For(target=ast.Tuple(elts=_elts), body=_body):
                        uuid4 = str(uuid.uuid4())[:5]
                        tmp_name_store = ast.Name(id=f'__TMP__{uuid4}', ctx=ast.Store())
                        tmp_name_load = ast.Name(id=tmp_name_store.id, ctx=ast.Load())
                        node.target = tmp_name_load
                        for i, name in enumerate(_elts):
                            assign = ast.Assign(targets=[name], value=ast.Subscript(value=tmp_name_load, slice=ast.Constant(value=i), ctx=ast.Load()), **position_args)
                            _body.insert(i, assign)
            
        return self.generic_visit(node)


# s = """
# x = 1
# x = y = 1
# x, y = 1, 2
# x, y = func()

# def foo():
#     a = 1
#     a, b, c = t
#     a = b = c = 1
# """
# syntax_tree = ast.parse(s)
# MultitargetTransformer().visit(syntax_tree)

# print(ast.dump(syntax_tree, indent=2))
# print(ast.unparse(syntax_tree))