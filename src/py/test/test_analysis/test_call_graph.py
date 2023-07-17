import unittest
import sys
sys.path.insert(0, 'src/py') # hack for now

import ast
from ast_utils.utils import *
from ast_utils.position_parent import *
from ast_utils.scoped_tree import get_scoped_tree

from analysis.call_graph import *

class TestCallGraph(unittest.TestCase):
    def test_1(self):
        source_code = """
def A():
    A()
def B():
    A()
    C()
def C():
    A() + B()
def D():
    A()
        """

        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = add_position_and_parent(parsed_ast, source_code, line_offsets)
        scoped_tree = get_scoped_tree(syntax_tree)

        A = scoped_tree.root_node.body[0]
        B = scoped_tree.root_node.body[1]
        C = scoped_tree.root_node.body[2]
        AB = C.body[0].value # (A() + B())
        D = scoped_tree.root_node.body[3]

        call_graph = compute_call_graph(scoped_tree.root_node, scoped_tree.scope_info, C)
        self.assertTrue(D not in call_graph)
        self.assertTrue(call_graph[A] == [A])
        self.assertTrue(call_graph[B] == [A,C])
        self.assertTrue(call_graph[C] == [A,B])

        call_graph = compute_call_graph(scoped_tree.root_node, scoped_tree.scope_info, D)
        self.assertTrue(B not in call_graph and C not in call_graph)
        self.assertTrue(call_graph[A] == [A])
        self.assertTrue(call_graph[D] == [A])

        call_graph = compute_call_graph(scoped_tree.root_node, scoped_tree.scope_info, AB)
        self.assertTrue(D not in call_graph)
        self.assertTrue(call_graph[A] == [A])
        self.assertTrue(call_graph[B] == [A,C])
        self.assertTrue(call_graph[C] == [A,B])

    def test_2(self):
        source_code = """
def A():
    A()
    return 'A'

def B():
    return A()

def C():
    def D():
        C()
        return B()
    def E():
        return D()
    return E()
"""

        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = add_position_and_parent(parsed_ast, source_code, line_offsets)
        scoped_tree = get_scoped_tree(syntax_tree)

        A = scoped_tree.root_node.body[0]
        B = scoped_tree.root_node.body[1]
        C = scoped_tree.root_node.body[2]
        D = C.body[0]
        E = C.body[1]

        call_graph = compute_call_graph(scoped_tree.root_node, scoped_tree.scope_info, C)

        self.assertTrue(call_graph[A] == [A])
        self.assertTrue(call_graph[B] == [A])
        self.assertTrue(call_graph[C] == [E])
        self.assertTrue(B in call_graph[D] and C in call_graph[D])
        self.assertTrue(call_graph[E] == [D])
