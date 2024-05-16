import unittest
import sys
sys.path.insert(0, 'src/py') # hack for now

import ast
from ast_utils.utils import *
from ast_utils.preprocess import *
from ast_utils.node_finder import NodeFinder

class TestUtils(unittest.TestCase):
    def test_get_name(self):
        source_code = "x = 1"
        node = ast.parse(source_code).body[0]
        self.assertEquals(get_name(node.targets[0]).id, "x")

        source_code = "x[i] = 1"
        node = ast.parse(source_code).body[0]
        self.assertEquals(get_name(node.targets[0]).id, "x")

        source_code = "x: int = 1" # ast.AnnAssign
        node = ast.parse(source_code).body[0]
        self.assertEquals(get_name(node.target).id, "x")

    def test_get_call_name(self):
        source_code = "func(x)"
        node = ast.parse(source_code).body[0].value
        self.assertEquals(get_call_name(node), "func")

        source_code = "module.func(x)"
        node = ast.parse(source_code).body[0].value
        self.assertEquals(get_call_name(node), "func")


    def test_block_and_is_different_branch(self):
        source_code = """
if test1:
    A
    B
else:
    C
    if test2:
        D
    else:
        E
    if test3:
        F
    if test4:
        pass
        """
        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = preprocess_syntaxtree(parsed_ast, source_code, line_offsets, 0)

        node = syntax_tree.root_node.body[0]

        A = node.body[0].value
        B = node.body[1].value
        C = node.orelse[0].value
        D = node.orelse[1].body[0].value
        E = node.orelse[1].orelse[0].value
        F = node.orelse[2].body[0].value
        # [ast.dump(n) for n in [A,B,C,D,E,F]]
        
        self.assertTrue(isinstance(node.body, Block)) # [A,B]
        self.assertTrue(len(node.body) == 2)
        self.assertTrue(node.body[0].value == A and node.body[1].value == B)
        self.assertTrue(is_descendant(node.body[0], A))
        self.assertTrue(isinstance(node.orelse, Block)) # [C, if ...]
        self.assertTrue(isinstance(node.orelse[1].body, Block)) # D
        self.assertTrue(isinstance(node.orelse[1].orelse, Block)) # E
        self.assertTrue(isinstance(node.orelse[3].body, Block)) # pass
        self.assertTrue(not hasattr(node.orelse[3], "orelse"))
        
        self.assertTrue(not is_in_different_branch(A,B))
        self.assertTrue(is_in_different_branch(A,C) and is_in_different_branch(A,D) and is_in_different_branch(A,E) and is_in_different_branch(A,F))
        self.assertTrue(not is_in_different_branch(C,F))
        self.assertTrue(is_in_different_branch(D,E))
        self.assertTrue(not is_in_different_branch(D,F))

#     def test_get_subnode_for_range(self):
#         source_code = """
# 1
# x = 1
# def test(a, b: int, c=1, d: int=1):
#     if a == 1:
#         y = 2
#     else:
#         x = 3
    
#     for i in range(b,f):
#         if i > 10:
#             break

#     while c > 2:
#         c = c - 1
# """
#         parsed_ast = ast.parse(source_code)
#         line_offsets = get_line_offsets_for_str(source_code)
#         _ = preprocess_syntaxtree(parsed_ast, source_code, line_offsets, 0)

#         def nodefinder_map(x):
#             print(ast.dump(x))
#             a, b = get_range(x)
#             print(a,b)
#             print(source_code[a:b])
#             return get_subnode_for_range(syntax_tree, a, b) == x

#         nodefinder = NodeFinder(lambda x: True, nodefinder_map, visit_matched_nodes=True)
#         nodefinder.visit(syntax_tree)
#         self.assertTrue(all(nodefinder.result))


