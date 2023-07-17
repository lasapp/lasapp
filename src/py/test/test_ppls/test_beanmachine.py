import unittest
import sys
sys.path.insert(0, 'src/py') # hack for now

import ast
from ast_utils.utils import *
from ast_utils.position_parent import *
from ppls import *

class TestPyro(unittest.TestCase):
    def test_1(self):
        source_code = """
@bm.random_variable
def x():
    return dist.Normal(0., 1.)

@bm.random_variable
def y():
    return dist.Gamma(1, 1)

@bm.random_variable
def e(i):
    return dist.Bernoulli(0.5)

observations = {y(): 1}
observations[e(1)] = 1
"""

        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = add_position_and_parent(parsed_ast, source_code, line_offsets)
        
        ppl_obj = Beanmachine()
        
        x_def = syntax_tree.root_node.body[0]
        y_def = syntax_tree.root_node.body[1]
        e_def = syntax_tree.root_node.body[2]
        
        dist_node = ppl_obj.get_distribution_node(VariableDefinition(x_def))
        self.assertEqual(ast.unparse(dist_node), "dist.Normal(0.0, 1.0)")
        dist_name, dist_params = ppl_obj.get_distribution(dist_node)
        self.assertEqual(dist_name,  "Normal")
        self.assertEqual(ast.unparse(dist_params["location"]),  "0.0")
        self.assertEqual(ast.unparse(dist_params["scale"]), "1.0")

        for (node, name, is_obs) in [(x_def,"x()",False), (y_def,"y()",True), (e_def, "e(i)",True)]:
            self.assertTrue(ppl_obj.is_random_variable_definition(node))
            variable = VariableDefinition(node)
            self.assertEqual(ppl_obj.get_random_variable_name(variable), name)
            self.assertEqual(ppl_obj.is_observed(variable), is_obs)

    
    def test_2(self):
        source_code = """
@bm.random_variable
def y(i):
    return dist.Bernoulli(0.5)

@bm.random_variable
def x():
    return dist.Bernoulli(0.5)

observations = {}
for i in range(10):
    observations[y(i)] = 1

def bla(observations):
    observations[x()] = 1
"""

        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = add_position_and_parent(parsed_ast, source_code, line_offsets)
        
        ppl_obj = Beanmachine()

        y_def = syntax_tree.root_node.body[0]
        self.assertTrue(ppl_obj.is_random_variable_definition(y_def))
        variable = VariableDefinition(y_def)
        self.assertEqual(ppl_obj.is_observed(variable), True)

        x_def = syntax_tree.root_node.body[1]
        self.assertTrue(ppl_obj.is_random_variable_definition(x_def))
        variable = VariableDefinition(x_def)
        self.assertEqual(ppl_obj.is_observed(variable), False)
