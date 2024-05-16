import unittest
import sys
sys.path.insert(0, 'src/py') # hack for now

import ast
from ast_utils.utils import *
from ast_utils.preprocess import *
from ppls import *

class TestPyro(unittest.TestCase):
    def test(self):
        source_code = """
def test():
    x = pyro.sample("x", dist.Normal(0., 1.))
    pyro.sample("y", dist.Gamma(1, 1), obs=1.)
    i = 1
    pyro.sample("z", dist.Bernoulli(0.5))
    pyro.sample(f"e_{i}", dist.Bernoulli(0.5))
"""

        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = preprocess_syntaxtree(parsed_ast, source_code, line_offsets, 0)
        
        ppl_obj = Pyro()
        syntax_tree = ppl_obj.preprocess_syntax_tree(syntax_tree)

        func = syntax_tree.root_node.body[0]
        self.assertTrue(ppl_obj.is_model(func))
        
        x_def = func.body[0]
        y_def = func.body[1]
        z_def = func.body[3]
        e_def = func.body[4]
        
        dist_node = ppl_obj.get_distribution_node(VariableDefinition(x_def))
        self.assertEqual(ast.unparse(dist_node), "dist.Normal(0.0, 1.0)")
        dist_name, dist_params = ppl_obj.get_distribution(dist_node)
        self.assertEqual(dist_name,  "Normal")
        self.assertEqual(ast.unparse(dist_params["location"]),  "0.0")
        self.assertEqual(ast.unparse(dist_params["scale"]), "1.0")

        for (node, name, is_obs) in [(x_def,"'x'",False), (y_def,"'y'",True), (z_def,"'z'",False), (e_def, "f'e_{i}'",False)]:
            self.assertTrue(ppl_obj.is_random_variable_definition(node))
            variable = VariableDefinition(node)
            self.assertEqual(ppl_obj.get_random_variable_name(variable), name)
            self.assertEqual(ppl_obj.is_observed(variable), is_obs)