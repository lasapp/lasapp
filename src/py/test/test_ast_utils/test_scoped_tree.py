import unittest
import sys
sys.path.insert(0, 'src/py') # hack for now

import ast
from ast_utils.utils import *
from ast_utils.preprocess import *
from ast_utils.node_finder import NodeFinder
from ast_utils.scoped_tree import *

class TestScopedTree(unittest.TestCase):
    def test_1(self):
        source_code = """
def outer():
    x = 1
    def inner(z):
        y = 2
        outer(y)
    inner(x)
end
        """
        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = preprocess_syntaxtree(parsed_ast, source_code, line_offsets, 0)
        scoped_tree = get_scoped_tree(syntax_tree)

        node = scoped_tree.root_node
        outer_def = node.body[0]
        inner_def = outer_def.body[1]
        inner_call = outer_def.body[2].value
        outer_call = inner_def.body[1].value
        x = inner_call.args[0]
        y = outer_call.args[0]
        
        self.assertTrue(scoped_tree.scope_info[outer_def] == scoped_tree.scope_info.global_scope)
        self.assertTrue(scoped_tree.scope_info[outer_call.func] == scoped_tree.scope_info.global_scope)

        self.assertTrue(scoped_tree.scope_info[inner_def].function_node == outer_def)
        self.assertTrue(scoped_tree.scope_info[inner_call.func].function_node == outer_def)

        self.assertTrue(scoped_tree.scope_info[x].function_node == outer_def)
        self.assertTrue(scoped_tree.scope_info[y].function_node == inner_def)

    def test_2(self):
        source_code = """
x = 1
a,b,c = 2,3,4
        """
        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = preprocess_syntaxtree(parsed_ast, source_code, line_offsets, 0)
        scoped_tree = get_scoped_tree(syntax_tree)
        self.assertEqual(len(scoped_tree.all_definitions), 5)
        self.assertTrue(scoped_tree.all_definitions[1].name.startswith('__TMP__'))
        self.assertEqual([ass.name for ass in scoped_tree.all_definitions], ['x', scoped_tree.all_definitions[1].name, 'a', 'b', 'c'])
