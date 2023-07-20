
# Assumptions:
# pure functions, no lambdas, definition only depends on previous definitions
# data dependencies are only captured if sample statement is assigned to program variable
# e.g. pyro.sample("x", pyro.Normal(pyro.sample("mu", pyro.Normal(0.,1.)), 1.))
# is valid pyro code, but dependencies are not captured (maybe in future SSA)
# data dependencies are not passed as via parameters to functions (function parameters have no data dependencies)

import ast
from ast_utils.node_finder import NodeFinder
from ast_utils.scoped_tree import ScopedTree
from ast_utils.utils import is_descendant, is_in_different_branch, get_name

def NameFinder():
    return NodeFinder(
        lambda node: isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load),
        lambda node: node)

def is_indexed_assignment(node: ast.AST) -> bool:
    if isinstance(node, ast.Assign):
        return isinstance(node.targets[0], ast.Subscript)
    return False    

def get_identifiers_node_depends_on(scoped_tree: ScopedTree, node: ast.AST):
    if isinstance(node, ast.Assign):
        assert len(node.targets) == 1
        lhs = node.targets[0]
        identifier = get_name(lhs)
        rhs = node.value
        lhs_deps = set(NameFinder().visit(lhs))
        lhs_deps.discard(identifier)
        rhs_deps = set(NameFinder().visit(rhs))
        return lhs_deps | rhs_deps
    
    if isinstance(node, ast.FunctionDef):
        return set()
    if isinstance(node, ast.If) or isinstance(node, ast.While):
        # if and while only depend on condition
        return set(NameFinder().visit(node.test))
    if isinstance(node, ast.For):
        # for only depends on range
        return set(NameFinder().visit(node.iter))
    
    # default: all identifiers in node that are loaded
    return set(NameFinder().visit(node))

def ReturnFinder(func: ast.FunctionDef):
    assert isinstance(func, ast.FunctionDef)
    return_finder = NodeFinder(
        lambda x: isinstance(x, ast.Return),
        lambda x: x,
        visit_predicate=lambda x: x == func or not isinstance(x, ast.FunctionDef)
    )
    return return_finder

def data_deps_for_func(scoped_tree: ScopedTree, node: ast.FunctionDef):
    # get all data dependencies of return statements
    return_finder = ReturnFinder(node)
    data_deps = set()
    for return_stmt in return_finder.visit(node):
        data_deps = data_deps | data_deps_for_node(scoped_tree, return_stmt)

    return data_deps
    
def data_deps_for_node(scoped_tree: ScopedTree, node: ast.AST):
    assert is_descendant(scoped_tree.root_node, node)

    if isinstance(node, ast.FunctionDef):
        return data_deps_for_func(scoped_tree, node)
    
    node_is_while_loop_test = isinstance(node.parent, ast.While) and node.parent.test == node

    # find all user defined identifiers in expression
    identifiers = {identifier for identifier in get_identifiers_node_depends_on(scoped_tree, node) if identifier.id in scoped_tree.all_user_symbols}

    data_deps = set()
    for identifier in identifiers:
        # find scope of identifier
        scope = scoped_tree.scope_info[identifier]

        # find all assignments in all scopes `identifier = ...` that occur before expression
        for definition in scoped_tree.all_definitions:
            # filter for assignments which correspond *exactly* to identifier
            def_scope = scoped_tree.scope_info[definition.identifier]
            if def_scope == scope and definition.name == identifier.id:
                if ((definition.node.position < node.position) or
                    (definition.node.position == node.position and is_indexed_assignment(node))):

                    # check if nodes are in mutually exclusive branches
                    if not is_in_different_branch(definition.node, node):
                        # expression depends on this assignment
                        data_deps.add(definition)

                if node_is_while_loop_test:
                    # node is test of a while loop, so it may depend on while body
                    if is_descendant(node.parent.body, definition.node):
                        data_deps.add(definition)

        # check if identifier is a user-defined function
        for function in scoped_tree.all_functions:
            def_scope = scoped_tree.scope_info[function.node]
            if def_scope == scope and function.name == identifier.id:
                data_deps.add(function)
                break
    
    return data_deps

def control_parents_for_func(scoped_tree: ScopedTree, node: ast.FunctionDef):
    # get all control dependencies of return statements
    return_finder = ReturnFinder(node)
    control_nodes = set()
    for return_stmt in return_finder.visit(node):
        for control_parent in control_parents_for_node(scoped_tree, return_stmt):
            control_nodes.add(control_parent)

    return list(control_nodes)

def control_parents_for_node(scoped_tree: ScopedTree, node: ast.AST):
    assert is_descendant(scoped_tree.root_node, node)

    if isinstance(node, ast.FunctionDef):
        return control_parents_for_func(scoped_tree, node)
    
    control_nodes = set()

    nodes_to_analyse = [node]

    # get encompassing function and find all return statements
    # return statments cause branching in control flow graph
    current_node = node
    parent_function = None
    while current_node.parent is not None:
        current_node = current_node.parent
        if isinstance(current_node, ast.FunctionDef):
            parent_function = current_node
            break
    if parent_function is not None:
        return_finder = ReturnFinder(parent_function)
        return_statments = [return_stmt for return_stmt in return_finder.visit(parent_function) if return_stmt.position < node.position]
        nodes_to_analyse += return_statments


    for node in nodes_to_analyse:
        current_node = node
        while current_node.parent is not None:
            if isinstance(current_node, ast.FunctionDef):
                break
            current_node = current_node.parent
            if isinstance(current_node, (ast.If, ast.While)) and node != current_node.test:
                control_nodes.add(current_node)
            if isinstance(current_node, ast.For) and node != current_node.iter:
                control_nodes.add(current_node)

    return list(control_nodes)


