import ast
from ast_utils.utils import Block

class CFGNode:
    def __init__(self, id: str, syntaxnode: ast.AST) -> None:
        self.id = id
        self.syntaxnode = syntaxnode
        self.parents = set()
        self.children = set()
        self.is_blocked = False
    def block(self):
        self.is_blocked = True
    def unblock(self):
        self.is_blocked = False
    def __repr__(self) -> str:
        return get_short_node_string(self)

class StartNode(CFGNode): pass
class EndNode(CFGNode): pass
class AssignNode(CFGNode): pass
class BranchNode(CFGNode):
    def __init__(self, id: str, syntaxnode: ast.AST) -> None:
        super().__init__(id, syntaxnode)
        self.join_node: CFGNode = None # to be set later
class JoinNode(CFGNode):
    def __init__(self, id: str, syntaxnode: ast.AST) -> None:
        super().__init__(id, syntaxnode)
        self.branch_node: CFGNode = None  # to be set later
class ReturnNode(CFGNode): pass
class BreakNode(CFGNode): pass
class ContinueNode(CFGNode): pass
class FuncStartNode(CFGNode): pass
class FuncArgNode(CFGNode): pass
class FuncJoinNode(CFGNode): pass
class ExprNode(CFGNode): pass
class LoopIterNode(CFGNode): pass

def get_short_node_string(node: CFGNode):
    s = type(node).__name__
    if isinstance(node, JoinNode) and isinstance(node.syntaxnode, ast.FunctionDef):
        return f"{s}({node.syntaxnode.name})"
    if isinstance(node, (AssignNode, BranchNode, JoinNode, ReturnNode, FuncArgNode, ExprNode)):
        return f"{s}({ast.unparse(node.syntaxnode)})"
    if isinstance(node, LoopIterNode):
        return f"{s}({ast.unparse(node.syntaxnode.target)} in {ast.unparse(node.syntaxnode.iter)})"
    else:
        return f"{s}()"

def add_edge(from_node: CFGNode, to_node: CFGNode):
    from_node.children.add(to_node)
    to_node.parents.add(from_node)

def delete_edge(from_node: CFGNode, to_node: CFGNode):
    from_node.children.discard(to_node)
    to_node.parents.discard(from_node)


# returns true if startnode is reachable from endnode
def _is_reachable(startnode: CFGNode, endnode: CFGNode, path: list[CFGNode]):
    if endnode.is_blocked:
        return False
    
    for parent in endnode.parents:
        if parent == startnode:
            return True
        is_cycle = any(p == parent for p in path)
        if not is_cycle:
            new_path = copy(path) if len(endnode.parents) > 1 else path
            new_path.append(parent)
            if _is_reachable(startnode, parent, new_path):
                return True
    return False

def is_reachable(startnode:CFGNode, endnode: CFGNode):
    return _is_reachable(startnode, endnode, [])

def is_on_path_between_nodes(node: CFGNode, startnode: CFGNode, endnode: CFGNode):
    return is_reachable(startnode, node) and is_reachable(node, endnode)

from typing import Set,Dict,Optional
class CFG:
    def __init__(self, startnode: StartNode, nodes: Set[CFGNode], endnode: EndNode) -> None:
        assert isinstance(startnode, (StartNode, FuncStartNode)), f"Wrong type for startnode {startnode}"
        assert isinstance(endnode, EndNode), f"Wrong type for endnode {endnode}"
        assert len(startnode.parents) == 0 and len(startnode.children) == 1
        assert len(endnode.parents) == 1 and len(endnode.children) == 0
        self.startnode = startnode
        self.nodes = nodes
        self.endnode = endnode

def verify_cfg(cfg: CFG):
    if not isinstance(cfg.startnode, (StartNode, FuncStartNode)):
        raise Exception(f"Startnode has wrong type: {cfg.startnode}")
    if not isinstance(cfg.endnode, EndNode):
        raise Exception("Endnode has wrong type: $(cfg.endnode.type)")
    if len(cfg.startnode.parents) != 0 or len(cfg.startnode.children) != 1:
        raise Exception(f"Startnode has wrong number of parents / children: {cfg.startnode.parents} / {cfg.startnode.children}")
    if len(cfg.endnode.parents) != 1 or len (cfg.endnode.children) != 0:
        raise Exception(f"Endnode has wrong number of parents / children: {cfg.endnode.parents} / {cfg.endnode.children}")
    
    for node in cfg.nodes:
        for parent in node.parents:
            if not (node in parent.children):
                raise Exception(f"{parent} is parent of node {node}, but {node} is not among its children {parent.children}") 
        for child in node.children:
            if not (node in child.parents):
                raise Exception(f"{child} is child of node {node}, but {node} is not among its parents {child.parents}") 

        if not isinstance(node, (BranchNode, JoinNode)):
            if len(node.parents) != 1 or len(node.parents) != 1:
                raise Exception(f"{node} has wrong number of parents / children: {node.parents} / {node.children}")

        if isinstance(node, JoinNode):
            if len(node.children) != 1:
                raise Exception(f"Joinnode {node} has wrong number of children: {node.children}")
            
        if isinstance(node, BranchNode):
            # assert that there is no branch node B2 such that
            # B1 -> ... B2 -> ... J1 -> ... J2
            b1 = node
            for b2 in cfg.nodes:
                if not isinstance(b2, BranchNode) or b1 == b2:
                    continue
                j1 = b1.join_node
                j2 = b2.join_node
                # all paths from b2 to j1 have to go through j2
                b1.block() # B2 -> ... B1 -> ... J1 -> ... J2
                j2.block()
                assert not is_reachable(b2, j1), f"{b2} can reach {j1} without going through its {j2} or {b1}."
                j2.unblock()
                b1.unblock()

    return True

def is_supported_expression(node: ast.AST):
    if not isinstance(node, (
        ast.Expr, ast.Import, ast.ImportFrom, # stmt
        ast.BoolOp, ast.NamedExpr, ast.BinOp, ast.UnaryOp, ast.Dict, ast.Set, ast.Compare, ast.Call, ast.JoinedStr, ast.FormattedValue,
        ast.Constant, ast.Attribute, ast.Subscript, ast.Name, ast.List, ast.Tuple, ast.Slice, # expr
        ast.expr_context, ast.boolop, ast.operator, ast.unaryop, ast.cmpop, ast.arguments, ast.arg, ast.keyword, ast.alias,
        ast.Pass
        )):
        print("Is unsupported expression", node)
        return False
    return all(is_supported_expression(child) for child in ast.iter_child_nodes(node))

EMPTY_RETURN_NODE = ast.Expr(value=ast.Constant(value=None))

def get_return_expr(cfgnode: ReturnNode):
    assert isinstance(cfgnode, ReturnNode)
    if isinstance(cfgnode.syntaxnode, ast.Return):
        if cfgnode.syntaxnode.value is not None:
            return cfgnode.syntaxnode.value
        else:
            return EMPTY_RETURN_NODE
    else:
        return cfgnode.syntaxnode # this comes from an EXPR_NODE which got transformed to RETURN_NODE

from copy import copy
class CFGBuilder():
    def __init__(self, node_to_id: Dict[ast.AST,str]) -> None:
        self.node_to_id = node_to_id
        self.cfgs = dict() # toplevel -> CFG, functiondef -> CFG

    def transform_expr_to_return_nodes(self, nodes, func_join_node, join_node):
        join_node_parents = copy(join_node.parents)
        for parent in join_node_parents:
            if isinstance(parent, ReturnNode):
                # is ok
                pass
            elif isinstance(parent, JoinNode):
                # there should be no cycles of only join nodes -> recusion is ok
                self.transform_expr_to_return_nodes(nodes, func_join_node, parent)
            else:
                if isinstance(parent, ExprNode):
                    # make expression node return node
                    return_node = ReturnNode(parent.id, parent.syntaxnode)
                else:
                    # @warn("Unsupported return statement $parent. Default to return nothing.")
                    return_node = ReturnNode(parent.id, EMPTY_RETURN_NODE)
                
                nodes.add(return_node)
                delete_edge(parent, join_node)
                add_edge(parent, return_node)
                add_edge(return_node, func_join_node)
            
        # it can happen that we fully eliminate join node
        # func join node forms branch join pair with every branch node anyways, so it is safe to remove
        # join nodes that are direct parents of func join node
        if len(join_node.parents) == 0:
            for child in join_node.children:
                child.parents.discard(join_node)

            join_node.children = set()
            nodes.discard(join_node)
        
        
    def get_function_cfg(self, node: ast.FunctionDef):
        node_id = self.node_to_id[node]
        func_signature = node
        func_body = node.body

        # all returns go to join node
        join_cfgnode = FuncJoinNode(node_id, func_signature)
        # return stmts "break" to join_node, no continuenode
        body_cfg = self.get_cfg(func_body, join_cfgnode, None)

        nodes = copy(body_cfg.nodes)
        nodes.add(join_cfgnode)

        # FUNCSTART -> FUNCARG1 -> FUNCARG2 ...
        startnode = FuncStartNode(node_id, node)
        current_node = startnode
        assert len(node.args.posonlyargs) == 0, f"Position only args are not supported yet. ({node.name, node.args.posonlyargs})"
        assert len(node.args.kwonlyargs) == 0, f"Keyword only args are not supported yet. ({node.name, node.args.kwonlyargs})"
        for p in node.args.args:
            funcarg_node_id = self.node_to_id[p]
            assert isinstance(p, ast.arg), f"Param {p} is not ast.arg"
            funcarg_node = FuncArgNode(funcarg_node_id, p)
            add_edge(current_node, funcarg_node)
            nodes.add(funcarg_node)
            current_node = funcarg_node
        
        endnode = EndNode(node_id, node)

        # join node takes all connections from body endnode
        for parent in copy(body_cfg.endnode.parents):
            if parent == join_cfgnode: continue
            add_edge(parent, join_cfgnode)
            delete_edge(parent, body_cfg.endnode)
        
        add_edge(join_cfgnode, body_cfg.endnode)

        # join node should only continue to end
        discard = [child for child in join_cfgnode.children if not isinstance(child, EndNode)]
        for child in discard:
            join_cfgnode.discard(child)
        
        N1 = list(body_cfg.startnode.children)[0] # node after start node
        N2 = list(body_cfg.endnode.parents)[0]    # node before end node
        assert N2 == join_cfgnode

        delete_edge(N2, body_cfg.endnode)
        delete_edge(body_cfg.startnode, N1)
        
        # FUNCARGS -> BODY
        add_edge(current_node, N1)
        # BODY -> JOIN_NODE -> END
        add_edge(N2, endnode) # N2 == join_cfgnode

        self.transform_expr_to_return_nodes(nodes, join_cfgnode, join_cfgnode)

        return CFG(startnode, nodes, endnode)

    def get_cfg(self, node: ast.AST, breaknode:Optional[CFGNode], continuenode:Optional[CFGNode]) -> CFG:
        node_id = self.node_to_id[node]

        startnode = StartNode(node_id, node)
        nodes = set()
        endnode = EndNode(node_id, node)

        if isinstance(node, ast.Module):
            cfg = self.get_cfg(node.body, None, None)
            self.cfgs[node] = cfg
            return cfg
        
        if isinstance(node, ast.With):
            return self.get_cfg(node.body, None, None)

        if isinstance(node, Block):
            # concatentate all children if they are not functions
            # S_i -> CFG_i -> E_i
            # => S -> CFG_1 -> ... CFG_n -> E
            current_node = startnode
            for child in node.elts:
                child_node_id = self.node_to_id[child]
                if isinstance(child, ast.FunctionDef):
                    function_cfg = self.get_function_cfg(child)
                    self.cfgs[child] = function_cfg
                
                elif isinstance(child, (ast.Return, ast.Break, ast.Continue)):
                    if isinstance(child, ast.Return):
                        special_node = ReturnNode(child_node_id, child)
                        goto_node = breaknode
                    elif isinstance(child, ast.Break):
                        special_node = BreakNode(child_node_id, child)
                        goto_node = breaknode
                    elif isinstance(child, ast.Continue):
                        special_node = ContinueNode(child_node_id, child)
                        goto_node = continuenode
                    
                    # CFG_i -> SPECIAL_NODE -> GOTO_NODE
                    nodes.add(special_node)
                    add_edge(current_node, special_node)
                    current_node = special_node
                    assert goto_node is not None
                    add_edge(current_node, goto_node)
                    break

                else:
                    child_cfg = self.get_cfg(child, breaknode, continuenode)
                    nodes = nodes.union(child_cfg.nodes)

                    N1 = list(child_cfg.startnode.children)[0] # node after start node
                    N2 = list(child_cfg.endnode.parents)[0]    # node before end node

                    delete_edge(child_cfg.startnode, N1)
                    add_edge(current_node, N1)
                    delete_edge(N2, child_cfg.endnode)
                    
                    # parents come from sub-cfg
                    current_node = N2

            if isinstance(current_node, (ast.Return, ast.Break)):
                add_edge(breaknode, endnode)
            elif isinstance(current_node, ast.Continue):
                add_edge(breaknode, endnode)
            else:
                add_edge(current_node, endnode)


        elif isinstance(node, ast.Assign):
            # S -> Assign -> E
            cfgnode = AssignNode(node_id, node)
            nodes.add(cfgnode)
            add_edge(startnode, cfgnode)
            add_edge(cfgnode, endnode)

        elif isinstance(node, ast.If):
            # S_true -> CFG_true -> E_true
            # S_false -> CFG_false -> E_false
            # CFG_false can be empty
            # =>
            # S -> Branch -> CFG_true -> Join -> E
            #             \> CFG_false /
            test_node = node.test
            
            branch_cfgnode = BranchNode(node_id, test_node)
            join_cfgnode = JoinNode(node_id, test_node)
            branch_cfgnode.join_node = join_cfgnode
            join_cfgnode.branch_node = branch_cfgnode

            nodes.update([branch_cfgnode, join_cfgnode])
            add_edge(startnode, branch_cfgnode)
            add_edge(join_cfgnode, endnode)
            
            branch_nodes = [node.body, node.orelse] if hasattr(node, "orelse") else [node.body]
            for branch_node in branch_nodes:
                # inherits breaknode and continuenode
                branch_cfg = self.get_cfg(branch_node, breaknode, continuenode)
                nodes = nodes.union(branch_cfg.nodes)

                N1 = list(branch_cfg.startnode.children)[0] # node after start node
                N2 = list(branch_cfg.endnode.parents)[0]    # node before end node

                delete_edge(branch_cfg.startnode, N1)
                delete_edge(N2, branch_cfg.endnode)

                add_edge(branch_cfgnode, N1)
                add_edge(N2, join_cfgnode)

            if not hasattr(node, "orelse"):
                # no alternate
                add_edge(branch_cfgnode, join_cfgnode)
            
        elif isinstance(node, ast.While):
            # S_body -> CFG_body -> E_body
            # => S -> Branch -> CFG_body \
            #           |   \<-----------/
            #            \> Join -> E   
            test_node = node.test

            branch_cfgnode = BranchNode(node_id, test_node)
            join_cfgnode = JoinNode(node_id, test_node)
            branch_cfgnode.join_node = join_cfgnode
            join_cfgnode.branch_node = branch_cfgnode

            nodes.update([branch_cfgnode, join_cfgnode])
            add_edge(startnode, branch_cfgnode)
            add_edge(join_cfgnode, endnode)

            body = node.body
            # continue stmts go to branch_cfgnode, break stmts go to join_cfgnode -> endnode
            body_cfg = self.get_cfg(body, join_cfgnode, branch_cfgnode)
            nodes = nodes.union(body_cfg.nodes)

            N1 = list(body_cfg.startnode.children)[0] # node after start node
            N2 = list(body_cfg.endnode.parents)[0]    # node before end node

            delete_edge(body_cfg.startnode, N1)
            delete_edge(N2, body_cfg.endnode)

            add_edge(branch_cfgnode, N1)
            add_edge(N2, branch_cfgnode)

            add_edge(branch_cfgnode, join_cfgnode)

            # join node should only continue to end
            discard = [child for child in join_cfgnode.children if not isinstance(child, EndNode)]
            for child in discard:
                join_cfgnode.children.discard(child)
                child.parents.discard(join_cfgnode)
        
        elif isinstance(node, ast.For):
            loop_var = node.iter
            body = node.body

            branch_cfgnode = BranchNode(node_id, loop_var)
            join_cfgnode = JoinNode(node_id, loop_var)
            branch_cfgnode.join_node = join_cfgnode
            join_cfgnode.branch_node = branch_cfgnode

            loop_var_cfgnode = LoopIterNode(node_id, node)

            # TODO: check loop range
            nodes.update([branch_cfgnode, join_cfgnode, loop_var_cfgnode])
            add_edge(startnode, branch_cfgnode)
            add_edge(join_cfgnode, endnode)

            # continue stmts go to branch_cfgnode, break stmts go to join_cfgnode -> endnode
            body_cfg = self.get_cfg(body, join_cfgnode, branch_cfgnode)
            nodes = nodes.union(body_cfg.nodes)

            N1 = list(body_cfg.startnode.children)[0] # node after start node
            N2 = list(body_cfg.endnode.parents)[0]    # node before end node

            delete_edge(body_cfg.startnode, N1)
            delete_edge(N2, body_cfg.endnode)

            add_edge(branch_cfgnode, loop_var_cfgnode)
            add_edge(loop_var_cfgnode, N1)
            add_edge(N2, branch_cfgnode)
            add_edge(branch_cfgnode, join_cfgnode)

            # join node should only continue to end
            discard = [child for child in join_cfgnode.children if not isinstance(child, EndNode)]
            for child in discard:
                join_cfgnode.children.discard(child)
                child.parents.discard(join_cfgnode)
            
        elif is_supported_expression(node):
            cfgnode = ExprNode(node_id, node)
            nodes.add(cfgnode)
            add_edge(startnode, cfgnode)
            add_edge(cfgnode, endnode)
        else:
            raise Exception(f"Unsupported node {node}")


        return CFG(startnode, nodes, endnode)
            
def get_cfg_representation(root_node: ast.AST, node_to_id: Dict[ast.AST, str]):
    cfgbuilder = CFGBuilder(node_to_id)
    cfgbuilder.get_cfg(root_node, None, None)
    return cfgbuilder.cfgs


def print_cfg_dot(cfg: CFG):
    print("digraph CFG {")
    print("node [shape=box];")
    edges = []
    for node in [cfg.startnode] + list(cfg.nodes) + [cfg.endnode]:
        for child in node.children:
            edges.append((node, child))

    for (node, child) in edges:
        print(f"\"{get_short_node_string(node)}_{node.id}\" -> \"{get_short_node_string(child)}_{child.id}\"")
    print("}")