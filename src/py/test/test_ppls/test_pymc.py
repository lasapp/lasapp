import unittest
import sys
sys.path.insert(0, 'src/py') # hack for now

import ast
from ast_utils.utils import *
from ast_utils.position_parent import *
from ppls import *

class TestPyMC(unittest.TestCase):
    def test(self):
        source_code = """
with pm.Model() as test:
    x = pm.Normal("x", mu=0., sigma=1.)
    pm.Gamma("y", shape=1, rate=1, observed=1.)
    i = 1
    e = pm.Bernoulli(f"e_{i}", dist.Bernoulli(0.5))
"""

        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = add_position_and_parent(parsed_ast, source_code, line_offsets)
        
        ppl_obj = PyMC()
        with_node = syntax_tree.root_node.body[0]
        self.assertTrue(ppl_obj.is_model(with_node))
        
        x_def = with_node.body[0]
        y_def = with_node.body[1].value
        e_def = with_node.body[3].value
        
        dist_node = ppl_obj.get_distribution_node(VariableDefinition(x_def))
        self.assertEqual(ast.unparse(dist_node), "pm.Normal('x', mu=0.0, sigma=1.0)")
        dist_name, dist_params = ppl_obj.get_distribution(dist_node)
        self.assertEqual(dist_name,  "Normal")
        self.assertEqual(ast.unparse(dist_params["location"]),  "0.0")
        self.assertEqual(ast.unparse(dist_params["scale"]), "1.0")

        for (node, name, is_obs) in [(x_def,"'x'",False), (y_def,"'y'",True), (e_def, "f'e_{i}'",False)]:
            self.assertTrue(ppl_obj.is_random_variable_definition(node))
            variable = VariableDefinition(node)
            self.assertEqual(ppl_obj.get_random_variable_name(variable), name)
            self.assertEqual(ppl_obj.is_observed(variable), is_obs)

    def test_2(self):
        source_code = """
with pm.Model() as test:
    x = pm.Uniform()
"""

        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = add_position_and_parent(parsed_ast, source_code, line_offsets)

        ppl_obj = PyMC()
        with_node = syntax_tree.root_node.body[0]

        x_def = with_node.body[0]

        dist_node = ppl_obj.get_distribution_node(VariableDefinition(x_def))
        self.assertRaises(Exception, ppl_obj.get_distribution, dist_node)
