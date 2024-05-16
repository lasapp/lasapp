import math
import ast
from ast_utils.node_finder import NodeFinder
from ast_utils.utils import get_assignment_name, get_name, get_call_name
from ast_utils.scoped_tree import ScopedTree, FunctionDefinition, NameFinder, is_referenced_identifier
from ast_utils.cfg import *
from copy import copy
from typing import Tuple, Optional

def get_cfgnode_target(cfgnode: CFGNode):
    if isinstance(cfgnode, AssignNode):
        return get_assignment_name(cfgnode.syntaxnode)
    elif isinstance(cfgnode, FuncArgNode):
        return cfgnode.syntaxnode
    elif isinstance(cfgnode, LoopIterNode):
        target = cfgnode.syntaxnode.target
        assert isinstance(target, ast.Name), f"Cannot get_assignnode_target for LoopIterNode {cfgnode}"
        return target
    else:
        raise Exception(f"Cannot get_assignnode_target for {cfgnode}")

def peval_ints(node: ast.AST):
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return peval_ints(node.left) + peval_ints(node.right)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Sub):
        return peval_ints(node.left) - peval_ints(node.right)
    return math.nan

def get_static_index_of_ref_identifier(identifier: ast.Name):
    ref_node = identifier.parent
    match ref_node:
        case ast.Subscript(slice=ast.Tuple(elts=_elts)):
            return [peval_ints(el) for el in _elts]
        case ast.Subscript(slice=_slice):
            return [peval_ints(_slice)]
    return math.nan

# only applicable for container variables
def point_to_same_element(identifier1: ast.Name, identifier2: ast.Name):
    if not (is_referenced_identifier(identifier1) and is_referenced_identifier(identifier2)):
        return False
    return get_static_index_of_ref_identifier(identifier1) == get_static_index_of_ref_identifier(identifier2)

def _get_RDs(scoped_tree: ScopedTree, cfgnode: CFGNode, identifier: ast.Name, path: list[CFGNode], rds: set[CFGNode], memo: dict[BranchNode, set[CFGNode]]):
    for parent in cfgnode.parents:
        if isinstance(parent, AssignNode):
            target = get_cfgnode_target(parent)
            if scoped_tree.identifieres_are_the_same(identifier, target):
                rds.add(parent)
                if not is_referenced_identifier(target):
                    continue
                if point_to_same_element(identifier, target):
                    continue
        elif isinstance(parent, (FuncArgNode, LoopIterNode)):
            target = get_cfgnode_target(parent)
            if scoped_tree.identifieres_are_the_same(identifier, target):
                rds.add(parent)
                continue
        
        is_cycle = any(p == parent for p in path)
        if not is_cycle:
            new_path = copy(path) if len(cfgnode.parents) > 1 else path
            new_path.append(parent)
            # we memoise at branch nodes to avoid path explosion
            if isinstance(parent, BranchNode):
                if parent in memo:
                    branch_rds = memo[parent]
                else:
                    branch_rds = _get_RDs(scoped_tree, parent, identifier, new_path, set(), memo)
                    memo[parent] = branch_rds
                rds.update(branch_rds)
            else:
                _get_RDs(scoped_tree, parent, identifier, new_path, rds, memo)
    return rds

def get_RDs(scoped_tree: ScopedTree, cfgnode: CFGNode, identifier: ast.Name):
    return _get_RDs(scoped_tree, cfgnode, identifier, [], set(), dict())

def _get_BPs(scoped_tree: ScopedTree, cfgnode: CFGNode, path: list[CFGNode], bps: set[CFGNode]):
    if isinstance(cfgnode, JoinNode):
        # j2 = cfgnode, b2 = cfgnode.branch_node
        # if there is a bp b1 on this path, then b1 -> ... b2 -> ... j2 -> ... node -> ... j1
        # since branch-join pairs cannot be interleaved (b1 cannot be on path between b2 and j2 - this is asserted in verify_cfg)
        # that is we can skip to b2 which greatly avoids path explosion
        return _get_BPs(scoped_tree, cfgnode.branch_node, path, bps)
    
    for parent in cfgnode.parents:
        if isinstance(parent, BranchNode):
            is_closed = any(p.branch_node == parent for p in path if isinstance(p, JoinNode))
            if not is_closed:
                # B -> ... -> node -> ... -> J
                bps.add(parent)
        
        is_cycle = any(p == parent for p in path)
        if not is_cycle:
            new_path = copy(path) if len(cfgnode.parents) > 1 else path
            new_path.append(parent)
            _get_BPs(scoped_tree, parent, new_path, bps)
    return bps

def get_BPs(scoped_tree: ScopedTree, cfgnode: CFGNode):
    return _get_BPs(scoped_tree, cfgnode, [], set())

def get_identifiers_read_in_syntaxnode(scoped_tree: ScopedTree, node: ast.AST):
    identifiers = None
    if isinstance(node, ast.Assign):
        assert len(node.targets) == 1
        lhs = node.targets[0]
        identifier = get_name(lhs)
        rhs = node.value
        lhs_deps = set(NameFinder().visit(lhs))
        lhs_deps.discard(identifier)
        rhs_deps = set(NameFinder().visit(rhs))
        identifiers = lhs_deps | rhs_deps
    
    elif is_supported_expression(node):
        identifiers = set(NameFinder().visit(node))

    else:
        raise Exception(f"Unsupported syntaxnode {node}")
    
    return set(i for i in identifiers if i.id in scoped_tree.all_user_symbols)

def find_call_sites_for_function(scoped_tree: ScopedTree, func_syntaxnode: ast.AST):
    assert isinstance(func_syntaxnode, ast.FunctionDef)
    call_finder = NodeFinder(
        lambda node: isinstance(node, ast.Call) and scoped_tree.identifieres_are_the_same(node.func, func_syntaxnode),
        lambda node: node
    )
    call_finder.visit(scoped_tree.root_node)
    return call_finder.result

def get_function_for_parameter(param_node: ast.arg):
     assert isinstance(param_node, ast.arg)
     args = param_node.parent
     assert isinstance(args, ast.arguments)
     func = args.parent
     return func

def get_matching_call_arg(param_node: ast.arg, call_site: ast.Call, func: ast.FunctionDef):
    assert isinstance(param_node, ast.arg)
    assert isinstance(call_site, ast.Call)
    assert isinstance(func, ast.FunctionDef)
    for kw in call_site.keywords:
        if kw.arg == param_node.arg:
            return kw
    assert len(func.args.posonlyargs) == 0, f"Position only args not supported yet {ast.unparse(func)}"
    param_names = [a.arg for a in func.args.args]
    param_ix = param_names.index(param_node.arg) # position of param in function signature
    if param_ix < len(call_site.args):
        # select param_ix-th argument in call site
        return call_site.args[param_ix]
    else:
        return None # has to have default argument

def get_all_exprs_passed_to_function_at_param(scoped_tree: ScopedTree, param_node: ast.arg):
    exprs = []
    func_syntaxnode = get_function_for_parameter(param_node)
    # in a pre-processing step we could duplicate the function for each of its calls
    # to make the following more precise, i.e. only <=1 call site per function
    call_sites = find_call_sites_for_function(scoped_tree, func_syntaxnode)
    for call_site in call_sites:
        matching_call_arg = get_matching_call_arg(param_node, call_site, func_syntaxnode)
        if matching_call_arg is not None:
            exprs.append(matching_call_arg)
    return exprs


def get_all_exprs_passed_to_function(scoped_tree: ScopedTree, func_syntaxnode: ast.AST):
    exprs =[]
    call_sites = find_call_sites_for_function(scoped_tree, func_syntaxnode)
    for call_site in call_sites:
        for call_arg in call_site.args + call_site.keywords:
            exprs.append(call_arg)
    return exprs

def data_deps_for_node(scoped_tree: ScopedTree, syntaxnode: ast.AST):
    if isinstance(syntaxnode, ast.FunctionDef):
        # union over data dependencies of all return statements
        cfg = scoped_tree.get_cfg_for_function_syntaxnode(syntaxnode)
        data_deps = set()
        for cfgnode in cfg.nodes:
            if isinstance(cfgnode, ReturnNode):
                data_deps = data_deps | _data_deps_for_node(scoped_tree, cfgnode, get_return_expr(cfgnode))
        return data_deps
    
    elif isinstance(syntaxnode, ast.arg):
        # union of expression corresponding to parameter in all calls
        data_deps = set()
        # return data_deps
        for expr in get_all_exprs_passed_to_function_at_param(scoped_tree, syntaxnode):
            _, cfgnode = scoped_tree.get_cfgnode_for_syntaxnode(expr)
            data_deps = data_deps | _data_deps_for_node(scoped_tree, cfgnode, expr)
        return data_deps
    
    elif isinstance(syntaxnode, ast.arguments):
        # union of expression corresponding to ALL parameters in all calls
        data_deps = set()
        # return data_deps
        func_syntaxnode = syntaxnode.parent
        for expr in get_all_exprs_passed_to_function(scoped_tree, func_syntaxnode):
            _, cfgnode = scoped_tree.get_cfgnode_for_syntaxnode(expr)
            data_deps = data_deps | _data_deps_for_node(scoped_tree, cfgnode, expr)
        return data_deps

    else:
        _, cfgnode = scoped_tree.get_cfgnode_for_syntaxnode(syntaxnode)
        return _data_deps_for_node(scoped_tree, cfgnode, syntaxnode)

def maybe_get_user_function(scoped_tree: ScopedTree, identifier) -> Tuple[bool, Optional[FunctionDefinition]]:
    for function in scoped_tree.all_functions:
        if scoped_tree.identifieres_are_the_same(identifier, function.node):
            return True, function
    return False, None

def _data_deps_for_node(scoped_tree: ScopedTree, cfgnode: CFGNode, syntaxnode: ast.AST):
    identifiers = get_identifiers_read_in_syntaxnode(scoped_tree, syntaxnode)

    data_deps = set()
    for identifier in identifiers:
        is_function, function = maybe_get_user_function(scoped_tree, identifier)
        if is_function:
            data_deps.add(function.node)
        else:
            rds = get_RDs(scoped_tree, cfgnode, identifier)
            for rd in rds:
                data_deps.add(rd.syntaxnode)

    return data_deps

def control_parents_for_node(scoped_tree: ScopedTree, syntaxnode: ast.AST):
    if isinstance(syntaxnode, ast.FunctionDef):
        cfg = scoped_tree.get_cfg_for_function_syntaxnode(syntaxnode)
        cfgnode = list(cfg.endnode.parents)[0] # function join node
        return _control_parents_for_node(scoped_tree, cfg, cfgnode)
    
    elif isinstance(syntaxnode, ast.arg) or isinstance(syntaxnode, ast.arguments):
        control_parents = set()
        # return set()
        func_syntaxnode = syntaxnode.parent if isinstance(syntaxnode, ast.arguments) else get_function_for_parameter(syntaxnode)
        call_sites = find_call_sites_for_function(scoped_tree, func_syntaxnode)
        for call_site in call_sites:
            control_parents = control_parents | control_parents_for_node(scoped_tree, call_site)
        return control_parents

    else:
        cfg, cfgnode = scoped_tree.get_cfgnode_for_syntaxnode(syntaxnode)
        return _control_parents_for_node(scoped_tree, cfg, cfgnode)

def _control_parents_for_node(scoped_tree: ScopedTree, cfg: CFG, cfgnode: CFGNode):
    assert cfgnode in cfg.nodes
    bps = get_BPs(scoped_tree, cfgnode)

    if isinstance(cfg.startnode, FuncStartNode):
        for branch_node in cfg.nodes:
            if not isinstance(branch_node, BranchNode):
                continue
            if is_on_path_between_nodes(cfgnode, branch_node, cfg.endnode):
                cfgnode.block()
                branch_node.join_node.block()
                if is_reachable(branch_node, cfg.endnode):
                    bps.add(branch_node)
                branch_node.join_node.unblock()
                cfgnode.unblock()

    return {bp.syntaxnode.parent for bp in bps}

