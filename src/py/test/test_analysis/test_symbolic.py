import unittest
import sys
sys.path.insert(0, 'src/py') # hack for now

import ast
from ast_utils.utils import *
from ast_utils.position_parent import *
from ast_utils.scoped_tree import get_scoped_tree

from analysis.symbolic import *


class TestSymblic(unittest.TestCase):
    def test_1(self):
        self.assertEqual(Symbol("X"), Symbol("X"))
        self.assertNotEqual(Symbol("X"), Symbol("X", "Int"))
        X = Symbol("X")
        self.assertEqual(Not(Not(X)), X)
        Y = Symbol("Y")
        self.assertEqual(Operation("f", X, Y),  Operation("f", X, Y))
        self.assertEqual(Not(Not(Operation("f", X, Y))), Operation("f", X, Y))
        self.assertNotEqual(Constant("X"), Symbol("X"))
        self.assertEqual(Constant(True), Constant(True))

    def test_2(self):
        source_code = """
def model(I: bool):
    A = pyro.sample('A', dist.Bernoulli(0.5))

    if A == 1:
        B = pyro.sample('B', dist.Normal(0., 1.))
    else:
        B = pyro.sample('B', dist.Gamma(1, 1))
        if B > 1 and I:
            pyro.sample('C', dist.Beta(1, 1))

    if B < 1 and I:
        pyro.sample('D', dist.Normal(0., 1.))
    if B < 2:
        pyro.sample('D', dist.Normal(0., 1.)) # Duplicated
        pyro.sample('E', dist.Normal(0., 1.))
        """

        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = add_position_and_parent(parsed_ast, source_code, line_offsets)
        scoped_tree = get_scoped_tree(syntax_tree)

        func = ast.parse(scoped_tree.root_node).body[0]
        A = func.body[0]
        B1 = func.body[1].body[0]
        B2 = func.body[1].orelse[0]
        C = func.body[1].orelse[1].body[0].value
        D1 = func.body[2].body[0].value
        D2 = func.body[3].body[0]
        E = func.body[3].body[1]
        node_to_symbol = {
            A: Symbol('A'),
            B1: Symbol('B'),
            B2: Symbol('B'),
            C: Symbol('C'),
            D1: Symbol('D'),
            D2: Symbol('D'),
            E: Symbol('E')
        }
        nodes = [A, B1, B2, C, D1, D2, E]

        result = {node: [] for node in nodes}
        evaluator = SymbolicEvaluator(result, func, node_to_symbol)
        evaluator.visit(func)
        self.assertEqual([len(evaluator.result[node]) for node in nodes], [12, 4, 8, 4, 6, 6, 6])
        
        result = get_path_condition_for_nodes(func, nodes, node_to_symbol)

        self.assertEqual(result[A],  Constant(True))
        self.assertEqual(result[B1], Operation("==", Symbol("A"), Constant(1)))
        self.assertEqual(result[B2], Not(Operation("==", Symbol("A"), Constant(1))))
        self.assertEqual(result[C], Operation("&", result[B2], Operation("&", Operation(">", Symbol("B"), Constant(1)), Symbol("I", "Bool"))))
        self.assertEqual(result[D1], Operation("&", Operation("<", Symbol("B"), Constant(1)), Symbol("I", "Bool")))
        self.assertEqual(result[D2], Operation("<", Symbol("B"), Constant(2)))
        self.assertEqual(result[E], Operation("<", Symbol("B"), Constant(2)))

    def test_3(self):
        source_code = """
def model(I):
    if I > 0:
        m = I-1
    else:
        m = 2*I
    
    if 0 < m:
        A = pyro.sample('A', dist.Bernoulli(0.5))
    else:
        B = pyro.sample('B', dist.Normal(0., 1.))
        """
        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = add_position_and_parent(parsed_ast, source_code, line_offsets)
        scoped_tree = get_scoped_tree(syntax_tree)

        func = scoped_tree.root_node.body[0]
        A = func.body[1].body[0].value
        B = func.body[1].orelse[0].value
        node_to_symbol = {
            A: Symbol('A'),
            B: Symbol('B')
        }
        nodes = [A,B]
        result = get_path_condition_for_nodes(func, nodes, node_to_symbol)
        self.assertEqual(path_condition_to_str(result[A]), "|(&(!(>(Real(I),Constant(0))),<(Constant(0),*(Constant(2),Real(I)))),&(>(Real(I),Constant(0)),<(Constant(0),-(Real(I),Constant(1)))))")
        self.assertEqual(path_condition_to_str(result[B]), "|(&(!(>(Real(I),Constant(0))),!(<(Constant(0),*(Constant(2),Real(I))))),&(>(Real(I),Constant(0)),!(<(Constant(0),-(Real(I),Constant(1))))))")
