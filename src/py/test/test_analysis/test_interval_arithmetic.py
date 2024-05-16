import unittest
import sys
sys.path.insert(0, 'src/py') # hack for now

import ast
from ast_utils.utils import *
from ast_utils.preprocess import *
from ast_utils.scoped_tree import get_scoped_tree

from analysis.interval_arithmetic import *

class TestIntervalArithmetic(unittest.TestCase):
    def test_1(self):
        self.assertEqual(add(Interval(-1,2), Interval(2,3)), Interval(1,5))
        self.assertEqual(mul(Interval(-1,2), Interval(2,3)), Interval(-3,6))
        self.assertEqual(sub(Interval(-1,2), Interval(2,3)), Interval(-4,0))
        self.assertEqual(div(Interval(-1,2), Interval(2,3)), Interval(-0.5, 1.0))
        self.assertEqual(mul(Interval(-1,2), Interval(3)), Interval(-3,6))
        self.assertEqual(union(Interval(-1,2), Interval(2,3)), Interval(-1,3))
        self.assertEqual(union(Interval(-1,2), Interval(3,4)), Interval(-1,4))
        self.assertEqual(pow(Interval(-1,2), Interval(2)), Interval(0,4))
        self.assertEqual(pow(Interval(-1,2), Interval(3)), Interval(-1,8))

    def test_2(self):
        source_code = """
a = x + y
b = a * z
exp(b)
        """
        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = preprocess_syntaxtree(parsed_ast, source_code, line_offsets, 0)
        scoped_tree = get_scoped_tree(syntax_tree)

        node_to_evaluate = scoped_tree.root_node.body[2].value
        x = Interval(-1,2)
        y = Interval(2,3)
        z = Interval(2)
        result = static_interval_eval(scoped_tree, node_to_evaluate, {"x": x, "y": y, "z": z})
        self.assertEqual(result, exp(mul(add(x, y), z)))

    
    def test_3(self):
        source_code = """
if x < 3:
    a = x + y
else:
    a = x - y
b = a * z
exp(b)
        """
        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = preprocess_syntaxtree(parsed_ast, source_code, line_offsets, 0)
        scoped_tree = get_scoped_tree(syntax_tree)

        node_to_evaluate = scoped_tree.root_node.body[2].value
        x = Interval(-1,2)
        y = Interval(2,3)
        z = Interval(2)
        result = static_interval_eval(scoped_tree, node_to_evaluate, {"x": x, "y": y, "z": z})
        self.assertEqual(result, exp(mul(union(add(x, y), sub(x, y)), z)))


    def test_4(self):
        source_code = """
if x < 3:
    a = x + y()
else:
    a = x - y()
b = a * z
exp(b)
        """
        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = preprocess_syntaxtree(parsed_ast, source_code, line_offsets, 0)
        scoped_tree = get_scoped_tree(syntax_tree)

        node_to_evaluate = scoped_tree.root_node.body[2].value
        x = Interval(-1,2)
        y = Interval(2,3)
        z = Interval(2)
        result = static_interval_eval(scoped_tree, node_to_evaluate, {"x": x, "y": y, "z": z})
        self.assertEqual(result, exp(mul(union(add(x, y), sub(x, y)), z)))