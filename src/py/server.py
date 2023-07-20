from jsonrpc_server import run_server, _SESSION

import ast
from ast_utils.scoped_tree import ScopedTree, get_scoped_tree
from ast_utils.position_parent import add_position_and_parent, SyntaxTree
from ast_utils.node_finders import VariableDefinitionCollector, find_model, find_guide
from ast_utils.utils import *

from analysis.call_graph import compute_call_graph
from analysis.data_control_flow import * 
import analysis.interval_arithmetic as interval_arithmetic
import analysis.symbolic as symbolic

from ppls import *
import server_interface
import uuid

def get_syntax_tree(file_content: str, line_offsets: list[int]) -> SyntaxTree:
    syntax_tree = ast.parse(file_content)
    syntax_tree = add_position_and_parent(syntax_tree, file_content, line_offsets)
    return syntax_tree

def get_variables(syntax_tree: SyntaxTree, ppl: PPL) -> list[VariableDefinition]:
    variable_collector = VariableDefinitionCollector(ppl)
    variable_collector.visit(syntax_tree.root_node)
    return variable_collector.result

def to_syntax_node(syntax_tree: SyntaxTree, node: ast.AST) -> server_interface.SyntaxNode:
    start, end = node.position, node.end_position
    node = server_interface.SyntaxNode(syntax_tree.node_to_id[node], start, end, source_text(node))
    return node

def to_random_variable(syntax_tree: SyntaxTree, variable: VariableDefinition, ppl: PPL, is_observed: bool) -> server_interface.RandomVariable:
    name = ppl.get_random_variable_name(variable)

    node = to_syntax_node(syntax_tree, variable.node)

    distribution_node = ppl.get_distribution_node(variable)
    dist_name, dist_params = ppl.get_distribution(distribution_node)

    distribution = server_interface.Distribution(
        dist_name,
        to_syntax_node(syntax_tree, distribution_node),
        [server_interface.DistributionParam(k, to_syntax_node(syntax_tree, v)) for k,v in dist_params.items()]
        )

    return server_interface.RandomVariable(node, name, distribution, is_observed)

_PPL_DICT =  {
    "pyro": Pyro(),
    "pymc": PyMC(),
    "beanmachine": Beanmachine()
}

def build_ast(file_name: str, ppl: str) -> str:
    print("build_ast")
    line_offsets = get_line_offsets(file_name)
    file_content = get_file_content(file_name)
    ppl_obj = _PPL_DICT[ppl]
    syntax_tree = get_syntax_tree(file_content, line_offsets)

    scoped_tree = get_scoped_tree(syntax_tree)
    uuid4 = str(uuid.uuid4())
    _SESSION[uuid4] = scoped_tree
    return uuid4

def get_model(file_name: str, ppl: str) -> server_interface.Model:
    print("get_model")
    line_offsets = get_line_offsets(file_name)
    file_content = get_file_content(file_name)
    ppl_obj =_PPL_DICT[ppl]
    syntax_tree = get_syntax_tree(file_content, line_offsets)

    model = find_model(syntax_tree.root_node, ppl_obj)

    return server_interface.Model(model.name, to_syntax_node(syntax_tree, model.node))


def get_guide(file_name: str, ppl: str) -> server_interface.Model:
    print("get_guide")
    line_offsets = get_line_offsets(file_name)
    file_content = get_file_content(file_name)
    ppl_obj =_PPL_DICT[ppl]
    syntax_tree = get_syntax_tree(file_content, line_offsets)

    model = find_guide(syntax_tree.root_node, ppl_obj)

    return server_interface.Model(model.name, to_syntax_node(syntax_tree, model.node))


def get_random_variables(file_name: str, ppl: str) -> list[server_interface.RandomVariable]:
    print("get_random_variables")
    line_offsets = get_line_offsets(file_name)
    file_content = get_file_content(file_name)
    ppl_obj =_PPL_DICT[ppl]
    syntax_tree = get_syntax_tree(file_content, line_offsets)

    variables = get_variables(syntax_tree, ppl_obj)

    response = []
    for variable in variables:
        v = to_random_variable(syntax_tree, variable, ppl_obj, ppl_obj.is_observed(variable))
        response.append(v)

    return response


def get_data_dependencies(tree_id: str, node: dict) -> list[server_interface.SyntaxNode]:
    print("get_data_dependencies")

    scoped_tree: ScopedTree = _SESSION[tree_id]
    node = scoped_tree.get_node_for_id(node["node_id"])
    data_deps = data_deps_for_node(scoped_tree, node)
    response = [to_syntax_node(scoped_tree.syntax_tree, dep.node) for dep in data_deps]
    return response

def get_control_parents(tree_id: str, node: dict) -> list[server_interface.ControlNode]:
    print("get_control_parents")

    scoped_tree: ScopedTree = _SESSION[tree_id]
    node = scoped_tree.get_node_for_id(node["node_id"])
    control_deps = control_parents_for_node(scoped_tree, node)
    response = []
    for dep in control_deps:
        if isinstance(dep, ast.If):
            kind = "if"
            control_subnode = dep.test
            body = [to_syntax_node(scoped_tree.syntax_tree, dep.body)]
            if hasattr(dep, "orelse"):
                body.append(to_syntax_node(scoped_tree.syntax_tree, dep.orelse))
        elif isinstance(dep, ast.While):
            kind = "while"
            control_subnode = dep.test
            body = [to_syntax_node(scoped_tree.syntax_tree, dep.body)]
        elif isinstance(dep, ast.For):
            kind = "for"
            control_subnode = dep.iter
            body = [to_syntax_node(scoped_tree.syntax_tree, dep.body)]
            
        response.append(server_interface.ControlNode(
            to_syntax_node(scoped_tree.syntax_tree, dep),
            kind,
            to_syntax_node(scoped_tree.syntax_tree, control_subnode),
            body
        ))

    return response

def estimate_value_range(tree_id: str, expr: dict, assumptions: list[tuple[dict, dict]]) -> server_interface.Interval:
    print("estimate_value_range")

    scoped_tree: ScopedTree = _SESSION[tree_id]
    # assumptions is a list[tuple[RandomVariable, Interval]]
    valuation = {}
    for rv, interval in assumptions:
        rv = server_interface.RandomVariable.from_dict(rv)
        interval = server_interface.Interval.from_dict(interval)
        parsed_interval = interval_arithmetic.Interval(float(interval.low), float(interval.high))
        rv_node = scoped_tree.get_node_for_id(rv.node.node_id)
        if isinstance(rv_node, ast.Assign):
            program_variable_symbol = get_assignment_name(rv_node).id
            valuation[program_variable_symbol] = parsed_interval
        elif isinstance(rv_node, ast.FunctionDef):
            program_variable_symbol = rv_node.name
            valuation[program_variable_symbol] = parsed_interval
        else:
            print(f"Cannot mask node of type {type(rv_node)}.")

    expr = server_interface.SyntaxNode.from_dict(expr)
    node_to_evaluate = scoped_tree.get_node_for_id(expr.node_id)

    res = interval_arithmetic.static_interval_eval(scoped_tree, node_to_evaluate, valuation)

    return server_interface.Interval(str(res.low), str(res.high))


def get_call_graph(tree_id: str, node: dict) -> list[server_interface.CallGraphNode]:
    print("get_call_graph")

    scoped_tree: ScopedTree = _SESSION[tree_id]
    node = scoped_tree.get_node_for_id(node["node_id"])

    call_graph = compute_call_graph(scoped_tree.root_node, scoped_tree.scope_info, node)

    call_nodes = []
    for caller, called in call_graph.items():
        call_nodes.append(server_interface.CallGraphNode(
            to_syntax_node(scoped_tree.syntax_tree, caller),
            [to_syntax_node(scoped_tree.syntax_tree, c) for c in called]
        ))
    
    return call_nodes


def get_path_conditions(tree_id: str, root: dict, nodes: list[dict], assumptions: list[tuple[dict, server_interface.SymbolicExpression]]) -> list[server_interface.SymbolicExpression]:
    print("get_path_conditions")
    scoped_tree: ScopedTree = _SESSION[tree_id]
    root = scoped_tree.get_node_for_id(root["node_id"])
    nodes = [scoped_tree.get_node_for_id(node["node_id"]) for node in nodes]
    node_to_symbol = {scoped_tree.get_node_for_id(node["node_id"]): symbolic.Symbol_from_str(sexp["expr"]) for node, sexp in assumptions}

    result = symbolic.get_path_condition_for_nodes(root, nodes, node_to_symbol)
    path_conditions = [server_interface.SymbolicExpression(symbolic.path_condition_to_str(result[node])) for node in nodes]
    return path_conditions

import sys
from jsonrpc import dispatcher
import os
from pathlib import Path

if __name__ == '__main__':
    # socket_name = sys.argv[1]
    Path("./.pipe").mkdir(exist_ok=True)
    socket_name = "./.pipe/python_rpc_socket"

    if os.path.exists(socket_name):
        os.remove(socket_name)

    print("Started Python Language Server", socket_name)

    dispatcher["build_ast"] = build_ast
    dispatcher["get_random_variables"] = get_random_variables
    dispatcher["get_model"] = get_model
    dispatcher["get_guide"] = get_guide
    dispatcher["get_data_dependencies"] = get_data_dependencies
    dispatcher["get_control_parents"] = get_control_parents
    dispatcher["estimate_value_range"] = estimate_value_range
    dispatcher["get_call_graph"] = get_call_graph
    dispatcher["get_path_conditions"] = get_path_conditions

    run_server(socket_name, dispatcher)