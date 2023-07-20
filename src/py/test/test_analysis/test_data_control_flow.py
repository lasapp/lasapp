import unittest
import sys
sys.path.insert(0, 'src/py') # hack for now

import ast
from ast_utils.utils import *
from ast_utils.position_parent import *
from ast_utils.scoped_tree import get_scoped_tree

from analysis.data_control_flow import *


class TestDataControlFlow(unittest.TestCase):
    def test_1(self):
        source_code = """
x = 1
y = x
        """
        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = add_position_and_parent(parsed_ast, source_code, line_offsets)
        scoped_tree = get_scoped_tree(syntax_tree)

        x_ass = parsed_ast.body[0]
        y_ass = parsed_ast.body[1]

        self.assertTrue(len(data_deps_for_node(scoped_tree, x_ass)) == 0)
        data_deps = list(data_deps_for_node(scoped_tree, y_ass))
        self.assertTrue(len(data_deps) == 1 and data_deps[0].node == x_ass)


    def test_2(self):
        source_code = """
x = 1
x = x
        """
        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = add_position_and_parent(parsed_ast, source_code, line_offsets)
        scoped_tree = get_scoped_tree(syntax_tree)

        x_ass = parsed_ast.body[0]
        x_ass_2 = parsed_ast.body[1]

        self.assertTrue(len(data_deps_for_node(scoped_tree, x_ass)) == 0)
        data_deps = list(data_deps_for_node(scoped_tree, x_ass_2))
        self.assertTrue(len(data_deps) == 1 and data_deps[0].node == x_ass)


    def test_3(self):
        source_code = """
x = 1
i = 1
y[i] = x
        """
        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = add_position_and_parent(parsed_ast, source_code, line_offsets)
        scoped_tree = get_scoped_tree(syntax_tree)

        x_ass = parsed_ast.body[0]
        i_ass = parsed_ast.body[1]
        y_ass = parsed_ast.body[2]

        self.assertTrue(len(data_deps_for_node(scoped_tree, x_ass)) == 0)
        data_deps = data_deps_for_node(scoped_tree, y_ass)
        self.assertTrue(len(data_deps.intersection([scoped_tree.all_definitions[i] for i in [0,1]])) == 2)

    def test_4(self):
        source_code = """
def outer():
    x = 1
    z = 1
    for i in range(10):
        y = i**2
        z = y
        """
        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = add_position_and_parent(parsed_ast, source_code, line_offsets)
        scoped_tree = get_scoped_tree(syntax_tree)

        outer = scoped_tree.root_node.body[0]
        for_loop = outer.body[2]
        y_ass = for_loop.body[0]
        i2 = y_ass.value.left
        z_ass = for_loop.body[1]
        y2 = z_ass.value

        self.assertTrue(len(scoped_tree.all_definitions) == 4) # no loop iter def
        self.assertTrue(len(data_deps_for_node(scoped_tree, i2)) == 0) # would be loop iter def 
        self.assertTrue(len(data_deps_for_node(scoped_tree, y_ass)) == 0) # would be loop iter def 
        self.assertTrue(data_deps_for_node(scoped_tree, y2) == set([scoped_tree.all_definitions[2]]))
        self.assertTrue(data_deps_for_node(scoped_tree, z_ass) == set([scoped_tree.all_definitions[2]]))

    def test_5(self):
        source_code = """
def outer():
    z = 1
    if z < 0:
        z = 2
    else:
        z = 3
        x = z
    y = z
        """
        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = add_position_and_parent(parsed_ast, source_code, line_offsets)
        scoped_tree = get_scoped_tree(syntax_tree)

        self.assertTrue(len(scoped_tree.all_definitions) == 5)
        
        outer = scoped_tree.root_node.body[0]
        x_ass = outer.body[1].orelse[1]
        y_ass = outer.body[2]
        
        data_deps = data_deps_for_node(scoped_tree, x_ass)
        self.assertTrue(len(data_deps) == 2 and len(data_deps.intersection([scoped_tree.all_definitions[i] for i in [0,2]])) == 2)

        data_deps = data_deps_for_node(scoped_tree, y_ass)
        self.assertTrue(len(data_deps) == 3 and len(data_deps.intersection(scoped_tree.all_definitions[:3])) == 3)

    def test_6(self):
        source_code = """
def A(y, z):
    return y + z

def B():
    y = 1
    z = 2
    x = A(y, z)
    """
        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = add_position_and_parent(parsed_ast, source_code, line_offsets)
        scoped_tree = get_scoped_tree(syntax_tree)
        
        x_ass = scoped_tree.root_node.body[1].body[2]
        
        self.assertTrue(len(scoped_tree.all_definitions) == 3 and len(scoped_tree.all_functions) == 2)
        
        data_deps = data_deps_for_node(scoped_tree, x_ass)

        self.assertTrue(len(data_deps) == 3)

        self.assertTrue(len(data_deps.intersection([
            scoped_tree.all_definitions[0],
            scoped_tree.all_definitions[1],
            scoped_tree.all_functions[0]
        ])) == 3)

    def test_7(self):
        source_code = """
def A():
    y = 1
    z = 2
    return y + z

def B(x):
    y = 1
    if x < 1:
        return y
    else:
        z = 2
        return z
        """
        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = add_position_and_parent(parsed_ast, source_code, line_offsets)
        scoped_tree = get_scoped_tree(syntax_tree)

        A = scoped_tree.root_node.body[0]
        B = scoped_tree.root_node.body[1]

        data_deps = data_deps_for_node(scoped_tree, A)
        self.assertTrue(len(data_deps) == 2)
        self.assertTrue(len(data_deps.intersection(scoped_tree.all_definitions[:2])) == 2)

        data_deps = data_deps_for_node(scoped_tree, B)
        self.assertTrue(len(data_deps) == 2)
        self.assertTrue(len(data_deps.intersection(scoped_tree.all_definitions[2:4])) == 2)

    def test_8(self):
        source_code = """
for i in range(10):
    if i < 5:
        j = 1
        while j < 3:
            j = 2
        """
        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = add_position_and_parent(parsed_ast, source_code, line_offsets)
        scoped_tree = get_scoped_tree(syntax_tree)
        
        for_node = scoped_tree.root_node.body[0]
        if_node = for_node.body[0]
        while_node = if_node.body[1]
        j = while_node.body[0]
        
        control_parents = control_parents_for_node(scoped_tree, j)
        self.assertTrue(set(control_parents) == set([while_node, if_node, for_node]))
        
    def test_9(self):
        source_code = """
def A(x, y):
    if x < 5:
        return 1
    if y < 5:
        return 2
        """
        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = add_position_and_parent(parsed_ast, source_code, line_offsets)
        scoped_tree = get_scoped_tree(syntax_tree)
        
        A = scoped_tree.root_node.body[0]
        if_1 = A.body[0]
        if_2 = A.body[1]

        control_parents = control_parents_for_node(scoped_tree, A)
        self.assertEqual(set(control_parents), set([if_1, if_2]))

    def test_10(self):
        source_code = """
x = 0
while x < 0.5:
    x = rand()
        """
        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = add_position_and_parent(parsed_ast, source_code, line_offsets)
        scoped_tree = get_scoped_tree(syntax_tree)

        while_node = scoped_tree.root_node.body[1]
        data_deps = data_deps_for_node(scoped_tree, while_node.test)
        x_zero = scoped_tree.root_node.body[0]
        x_rand = while_node.body[0]
        data_deps_nodes = [dep.node for dep in data_deps]
        self.assertIn(x_zero, data_deps_nodes)
        self.assertIn(x_rand, data_deps_nodes)


    def test_11(self):
        source_code = """
def A(x, y):
    if x < 5:
        return 1
    def B():
        if y < 5:
            return 2
        """
        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = add_position_and_parent(parsed_ast, source_code, line_offsets)
        scoped_tree = get_scoped_tree(syntax_tree)
        
        A = scoped_tree.root_node.body[0]
        if_1 = A.body[0]

        control_parents = control_parents_for_node(scoped_tree, A)
        self.assertTrue(control_parents == [if_1])


    def test_12(self):
        source_code = """
def A(x, y):
    if x < 5:
        return 1
    def B():
        if y < 5:
            return 2
    z = 3
        """
        parsed_ast = ast.parse(source_code)
        line_offsets = get_line_offsets_for_str(source_code)
        syntax_tree = add_position_and_parent(parsed_ast, source_code, line_offsets)
        scoped_tree = get_scoped_tree(syntax_tree)
        
        A = scoped_tree.root_node.body[0]
        if_1 = A.body[0]
        z = A.body[2]

        control_parents = control_parents_for_node(scoped_tree, z)
        self.assertTrue(control_parents == [if_1])