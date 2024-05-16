const CFGNodeType = UInt8
const START_NODE = CFGNodeType(0)
const END_NODE = CFGNodeType(1)
const ASSIGN_NODE = CFGNodeType(2)
const BRANCH_NODE = CFGNodeType(3)
const JOIN_NODE = CFGNodeType(4)
const RETURN_NODE = CFGNodeType(5)
const BREAK_NODE = CFGNodeType(6)
const CONTINUE_NODE = CFGNodeType(7)
const FUNCSTART_NODE = CFGNodeType(8)
const FUNCARG_NODE = CFGNodeType(9)
const EXPR_NODE = CFGNodeType(10) # no ops

const CFGNODE_TO_NAME = Dict(
    START_NODE => "START",
    END_NODE => "END",
    ASSIGN_NODE => "ASSIGN",
    BRANCH_NODE => "BRANCH",
    JOIN_NODE => "JOIN",
    RETURN_NODE => "RETURN",
    BREAK_NODE => "BREAK",
    CONTINUE_NODE => "CONTINUE",
    FUNCSTART_NODE => "FUNCSTART",
    FUNCARG_NODE => "FUNCARG",
    EXPR_NODE => "EXPR"
)

mutable struct CFGNode
    id::String # inherit id from syntaxnode
    syntaxnode::SyntaxNode
    type::CFGNodeType
    parents::Set{CFGNode}
    children::Set{CFGNode}
    is_blocked::Bool # may be used to stop traversal of CFG

    function CFGNode(id::String, syntaxnode::SyntaxNode, type::CFGNodeType, parents::Set{CFGNode}=Set{CFGNode}(), children::Set{CFGNode}=Set{CFGNode}(), is_blocked::Bool=false)
        return new("$(CFGNODE_TO_NAME[type])_$id", syntaxnode, type, parents, children, is_blocked)
    end

end

function add_edge!(from::CFGNode, to::CFGNode)
    push!(from.children, to)
    push!(to.parents, from)
end

function delete_edge!(from::CFGNode, to::CFGNode)
    delete!(from.children, to)
    delete!(to.parents, from)
end

function short_node_string(cfgnode::CFGNode)
    s = CFGNODE_TO_NAME[cfgnode.type]
    if cfgnode.type in (ASSIGN_NODE, BRANCH_NODE, JOIN_NODE, RETURN_NODE, FUNCARG_NODE, EXPR_NODE)
        s = s * "(" * JuliaSyntax.sourcetext(cfgnode.syntaxnode) * ")"
    end
    return s
end

function Base.show(io::IO, cfgnode::CFGNode)
    s = short_node_string(cfgnode)
    # type_str = CFGNODE_TO_NAME[cfgnode.type]
    # abbr_id = cfgnode.id[length(type_str):end]
    print(io, s, "@", cfgnode.id)
end

struct CFG
    startnode::CFGNode
    nodes::Set{CFGNode} # all nodes in cfg except start and end node
    # branchjoin_pairs::Set{Pair{CFGNode,CFGNode}}
    endnode::CFGNode
    function CFG(startnode::CFGNode, nodes::Set{CFGNode}, endnode::CFGNode)
        @assert startnode.type == START_NODE || startnode.type == FUNCSTART_NODE
        @assert endnode.type == END_NODE
        @assert length(startnode.parents) == 0 startnode.parents
        @assert length(startnode.children) == 1 startnode.children
        @assert length(endnode.parents) == 1 endnode.parents
        @assert length(endnode.children) == 0 endnode.children
        for node in nodes
            for parent in node.parents
                @assert node in parent.children (node, parent, parent.children)
            end
            for child in node.children
                @assert node in child.parents (node, child, child.parents)
            end
        end
        return new(startnode, nodes, endnode)
    end
end

function verify_cfg(cfg::CFG)
    if cfg.startnode.type != START_NODE && cfg.startnode.type != FUNCSTART_NODE
        error("Startnode has wrong type: $(cfg.startnode.type)")
    end
    if cfg.endnode.type != END_NODE
        error("Endnode has wrong type: $(cfg.endnode.type)")
    end
    if length(cfg.startnode.parents) != 0 || length(cfg.startnode.children) != 1
        error("Startnode has wrong number of parents / children: $(cfg.startnode.parents) / $(cfg.startnode.children)")
    end
    if length(cfg.endnode.parents) != 1 || length(cfg.endnode.children) != 0
        error("Endnode has wrong number of parents / children: $(cfg.endnode.parents) / $(cfg.endnode.children)")
    end
    
    for node in cfg.nodes
        for parent in node.parents
            if !(node in parent.children)
                error("$parent is parent of node $node, but $node is not among its children $(parent.children)") 
            end
        end
        for child in node.children
            if !(node in child.parents)
                error("$child is child of node $node, but $node is not among its parents $(child.parents)") 
            end
        end

        if !(node.type in (BRANCH_NODE, JOIN_NODE))
            if length(node.parents) != 1 || length(node.parents) != 1
                error("$node has wrong number of parents / children: $(node.parents) / $(node.children)")
            end
        end
        if node.type == JOIN_NODE
            if length(node.children) != 1
                error("Joinnode $node has wrong number of children: $(node.children)")
            end
        end
    end

    return true
end

function Base.show(io::IO, cfg::CFG)
    println(io, "CFG:")
    print(io, cfg.startnode, " -> ")
    join(io, repr.(cfg.startnode.children), ", ")
    println(io)
    for node in cfg.nodes
        print(io, node, " -> ")
        join(io, repr.(node.children), ", ")
        println(io)
    end
    println(io, cfg.endnode)
end

mutable struct CFGBuilder <: NodeVisitor
    scoped_tree::ScopedTree
    cfgs::Dict{SyntaxNode,CFG} # identifier -> root cfg node
end

# check if syntax node is expression (not a statement)
function is_supported_expression(node::SyntaxNode)
    node_kind = kind(node)
    if JuliaSyntax.is_literal(node_kind)
        return true
    elseif node_kind == K"string"
        # literal string or identifier for "$x" etc.
        return all(is_supported_expression(child) for child in JuliaSyntax.children(node))
    elseif node_kind == K"quote"
        return is_supported_expression(node[1])
    elseif is_variable_identifier(node)
        return true
    elseif node_kind == K"Identifier" && kind(node.parent) == K"quote"
        return true # literal symbols
    elseif node_kind == K"ref"
        # x[i]
        # for Int[] -> (ref Int) there is no node[2]
        return all(is_supported_expression(child) for child in JuliaSyntax.children(node))
    elseif node_kind == K"call" || node_kind == K"dotcall"
        for child in JuliaSyntax.children(node)
            if kind(child) == K"=" # keyword argument
                expr = child[2] # rhs
            else
                expr = child
            end
            if !is_supported_expression(expr)
                return false
            end
        end
        return true
    elseif node_kind == K"parameters" && kind(node.parent) == K"call" # keyword paramter in call f(; x = 1)
        return all(is_supported_expression(child) for child in JuliaSyntax.children(node))
    elseif JuliaSyntax.is_operator(node_kind)
        return all(is_supported_expression(child) for child in JuliaSyntax.children(node))
    elseif node_kind == K"vect" || node_kind == K"tuple"
        return all(is_supported_expression(child) for child in JuliaSyntax.children(node))
    elseif node_kind == K"macrocall" && is_supported_expression(node[2]) # e.g. @macro test(), not @macro function ...
        return true
    elseif node_kind == K"curly"
        return true # generic types
    elseif node_kind == K"juxtapose"
        return true # e.g. dot products written as x'y
    elseif node_kind == K"braces"
        return all(is_supported_expression(child) for child in JuliaSyntax.children(node))
    # elseif node_kind == K"comprehension"
    #     return true # TODO: consider control flow of array comprehension DISALLOW?
    elseif node_kind == K"hcat"
        # [a b]
        return all(is_supported_expression(child) for child in JuliaSyntax.children(node))
    else
        println("Unsupported expression: ", node, " - ", node_kind)
        return false
    end
end

const EMPTY_RETURN_NODE = get_empty_syntax_node(K"Identifier", val=:nothing)

# we assume that last statements of function body are return stmts or supported expressions
# if a non-return stmt (expr node) is successor of func join node: EXPR -> FUNCJOIN
# we add a return node: EXPR -> RETURN -> FUNCJOIN
# if there are multiple join nodes EXPR -> JOIN -> JOIN -> FUNCJOIN
# we still map EXPR -> RETURN -> FUNCJOIN and maybe remove the join nodes on the path
function transform_expr_to_return_nodes!(nodes::Set{CFGNode}, func_join_node::CFGNode, join_node::CFGNode)
    join_node_parents = copy(join_node.parents)
    for parent in join_node_parents
        if parent.type == RETURN_NODE
            # is ok
        elseif parent.type == JOIN_NODE
            # there should be no cycles of only join nodes -> recusion is ok
            transform_expr_to_return_nodes!(nodes, func_join_node, parent)
        else
            if parent.type == EXPR_NODE
                # make expression node return node
                return_node = CFGNode(parent.id, parent.syntaxnode, RETURN_NODE)
            else
                # @warn("Unsupported return statement $parent. Default to return nothing.")
                return_node = CFGNode(parent.id, EMPTY_RETURN_NODE, RETURN_NODE)
            end
            push!(nodes, return_node)
            delete_edge!(parent, join_node)
            add_edge!(parent, return_node)
            add_edge!(return_node, func_join_node)
        end
    end
    # it can happen that we fully eliminate join node
    # func join node forms branch join pair with every branch node anyways, so it is safe to remove
    # join nodes that are direct parents of func join node
    if isempty(join_node.parents)
        for child in join_node.children
            delete!(child.parents, join_node)
        end
        empty!(join_node.children)
        delete!(nodes, join_node)
    end
end

function get_return_expr(cfgnode::CFGNode)
    @assert cfgnode.type == RETURN_NODE
    if kind(cfgnode.syntaxnode) == K"return"
        if length(JuliaSyntax.children(cfgnode.syntaxnode)) == 1
            return cfgnode.syntaxnode[1]
        else
            return EMPTY_RETURN_NODE
        end
    else
        return cfgnode.syntaxnode # this comes from an EXPR_NODE which got transformed to RETURN_NODE
    end
end

function get_function_cfg(cfgbuilder::CFGBuilder, node::SyntaxNode)
    node_id = get_id_for_node(cfgbuilder.scoped_tree, node)
    func_signature = node[1]
    func_body = node[2]

    # all returns go to join node
    join_cfgnode = CFGNode(node_id, func_signature, JOIN_NODE)
    # return stmts "break" to join_node, no continuenode
    body_cfg = get_cfg(cfgbuilder, func_body, join_cfgnode, nothing)

    nodes = copy(body_cfg.nodes)
    push!(nodes, join_cfgnode)

    # FUNCSTART -> FUNCARG1 -> FUNCARG2 ...
    startnode = CFGNode(node_id, node, FUNCSTART_NODE)
    current_node = startnode
    for p in get_parameter_nodes_of_function(node)
        funcarg_node_id = get_id_for_node(cfgbuilder.scoped_tree, p)
        funcarg_node = CFGNode(funcarg_node_id, p, FUNCARG_NODE)
        add_edge!(current_node, funcarg_node)
        push!(nodes, funcarg_node)
        current_node = funcarg_node
    end

    endnode = CFGNode(node_id, node, END_NODE)

    # join node takes all connections from body endnode
    for parent in copy(body_cfg.endnode.parents)
        parent == join_cfgnode && continue
        add_edge!(parent, join_cfgnode)
        delete_edge!(parent, body_cfg.endnode)
    end
    add_edge!(join_cfgnode, body_cfg.endnode)

    # join node should only continue to end
    discard = [child for child in join_cfgnode.children if child.type != END_NODE]
    for child in discard
        delete_edge!(join_cfgnode, child)
    end

    N1 = first(body_cfg.startnode.children) # node after start node
    N2 = first(body_cfg.endnode.parents)    # node before end node
    @assert N2 == join_cfgnode

    delete_edge!(N2, body_cfg.endnode)
    delete_edge!(body_cfg.startnode, N1)
    
    # FUNCARGS -> BODY
    add_edge!(current_node, N1)
    # BODY -> JOIN_NODE -> END
    add_edge!(N2, endnode) # N2 == join_cfgnode

    transform_expr_to_return_nodes!(nodes, join_cfgnode, join_cfgnode)

    return CFG(startnode, nodes, endnode)
end

function get_cfg(cfgbuilder::CFGBuilder, node::SyntaxNode, breaknode::Union{Nothing,CFGNode}, continuenode::Union{Nothing,CFGNode})::CFG
    node_kind = kind(node)
    node_id = get_id_for_node(cfgbuilder.scoped_tree, node)
    startnode = CFGNode(node_id, node, START_NODE)   # S
    nodes = Set{CFGNode}()                           # CFG
    endnode = CFGNode(node_id, node, END_NODE)       # E

    if node_kind == K"toplevel" || node_kind == K"block"
        # concatentate all children if they are not functions
        # S_i -> CFG_i -> E_i
        # => S -> CFG_1 -> ... CFG_n -> E
        current_node = startnode
        for child in JuliaSyntax.children(node)
            child_node_id = get_id_for_node(cfgbuilder.scoped_tree, child)
            child_kind = kind(child)
            # functions get their own CFG
            if child_kind == K"function"
                function_cfg = get_function_cfg(cfgbuilder, child)
                cfgbuilder.cfgs[child] = function_cfg
            elseif child_kind == K"macrocall" && kind(child[2]) == K"function"
                function_cfg = get_function_cfg(cfgbuilder, child[2])
                cfgbuilder.cfgs[child[2]] = function_cfg

            # return, break, and continue stmts need specific control flow
            elseif child_kind in (K"return", K"break", K"continue")
                if child_kind == K"return"
                    special_node = CFGNode(child_node_id, child, RETURN_NODE)
                    goto_node = breaknode # successor of return stmt is breaknode
                elseif child_kind == K"break"
                    special_node = CFGNode(child_node_id, child, BREAK_NODE)
                    goto_node = breaknode # successor of break stmt is breaknode
                elseif child_kind == K"continue"
                    special_node = CFGNode(child_node_id, child, CONTINUE_NODE)
                    goto_node = continuenode # successor of continue stmt is continuenode
                end
                # CFG_i -> SPECIAL_NODE -> GOTO_NODE
                push!(nodes, special_node)
                add_edge!(current_node, special_node)
                current_node = special_node
                @assert !isnothing(goto_node)
                add_edge!(current_node, goto_node)
                break

            else
                child_cfg = get_cfg(cfgbuilder, child, breaknode, continuenode)
                nodes = nodes ∪ child_cfg.nodes

                N1 = first(child_cfg.startnode.children) # node after start node
                N2 = first(child_cfg.endnode.parents)    # node before end node

                delete_edge!(child_cfg.startnode, N1)
                add_edge!(current_node, N1)
                delete_edge!(N2, child_cfg.endnode)
                
                # parents come from sub-cfg
                current_node = N2
            end
        end

        if current_node.type in (RETURN_NODE, BREAK_NODE)
            add_edge!(breaknode, endnode)
        elseif current_node.type == CONTINUE_NODE
            # this is a technicality
            # endnode needs a parent, but current_node (CONTINUE_NODE) cannot be its parent
            add_edge!(breaknode, endnode)
        else
            add_edge!(current_node, endnode)
        end
    
    elseif JuliaSyntax.is_prec_assignment(node_kind)
        # S -> Assign -> E
        cfgnode = CFGNode(node_id, node, ASSIGN_NODE)
        push!(nodes, cfgnode)
        add_edge!(startnode, cfgnode)
        add_edge!(cfgnode, endnode)

        @assert length(JuliaSyntax.children(node)) == 2
        rhs = node[2]
        @assert is_supported_expression(rhs) "Unsupported expression on rhs of assignment $rhs"
    
    elseif node_kind == K"if" || node_kind == K"elseif"
        # S_true -> CFG_true -> E_true
        # S_false -> CFG_false -> E_false
        # CFG_false can be empty
        # =>
        # S -> Branch -> CFG_true -> Join -> E
        #             \> CFG_false /
        test_node = node[1]
        @assert is_supported_expression(test_node)
        
        branch_cfgnode = CFGNode(node_id, test_node, BRANCH_NODE)
        join_cfgnode = CFGNode(node_id, test_node, JOIN_NODE)
        push!(nodes, branch_cfgnode, join_cfgnode)
        add_edge!(startnode, branch_cfgnode)
        add_edge!(join_cfgnode, endnode)
        
        for branch_node in JuliaSyntax.children(node)[2:end]
            # inherits breaknode and continuenode
            branch_cfg = get_cfg(cfgbuilder, branch_node, breaknode, continuenode)
            nodes = nodes ∪ branch_cfg.nodes

            N1 = first(branch_cfg.startnode.children) # node after start node
            N2 = first(branch_cfg.endnode.parents)    # node before end node

            delete_edge!(branch_cfg.startnode, N1)
            delete_edge!(N2, branch_cfg.endnode)

            add_edge!(branch_cfgnode, N1)
            add_edge!(N2, join_cfgnode)

        end

        if length(JuliaSyntax.children(node)) == 2
            # no alternate
            add_edge!(branch_cfgnode, join_cfgnode)
        end

    elseif node_kind == K"while"
        # S_body -> CFG_body -> E_body
        # => S -> Branch -> CFG_body \
        #           |   \<-----------/
        #            \> Join -> E   
        test_node = node[1]
        @assert is_supported_expression(test_node)

        branch_cfgnode = CFGNode(node_id, test_node, BRANCH_NODE)
        join_cfgnode = CFGNode(node_id, test_node, JOIN_NODE)
        push!(nodes, branch_cfgnode, join_cfgnode)
        add_edge!(startnode, branch_cfgnode)
        add_edge!(join_cfgnode, endnode)

        body = node[2]
        # continue stmts go to branch_cfgnode, break stmts go to join_cfgnode -> endnode
        body_cfg = get_cfg(cfgbuilder, body, join_cfgnode, branch_cfgnode)
        nodes = nodes ∪ body_cfg.nodes

        N1 = first(body_cfg.startnode.children) # node after start node
        N2 = first(body_cfg.endnode.parents)    # node before end node

        delete_edge!(body_cfg.startnode, N1)
        delete_edge!(N2, body_cfg.endnode)

        add_edge!(branch_cfgnode, N1)
        add_edge!(N2, branch_cfgnode)

        add_edge!(branch_cfgnode, join_cfgnode)

        # join node should only continue to end
        discard = [child for child in join_cfgnode.children if child.type != END_NODE]
        for child in discard
            delete!(join_cfgnode.children, child)
            delete!(child.parents, join_cfgnode)
        end
    
    elseif node_kind == K"for"
        loop_var = node[1]
        body = node[2]

        branch_cfgnode = CFGNode(node_id, loop_var, BRANCH_NODE)
        join_cfgnode = CFGNode(node_id, loop_var, JOIN_NODE)
        loop_var_cfgnode = CFGNode(node_id, loop_var, ASSIGN_NODE)

        # TODO: check loop range
        push!(nodes, branch_cfgnode, join_cfgnode, loop_var_cfgnode)
        add_edge!(startnode, branch_cfgnode)
        add_edge!(join_cfgnode, endnode)

        # continue stmts go to branch_cfgnode, break stmts go to join_cfgnode -> endnode
        body_cfg = get_cfg(cfgbuilder, body, join_cfgnode, branch_cfgnode)
        nodes = nodes ∪ body_cfg.nodes

        N1 = first(body_cfg.startnode.children) # node after start node
        N2 = first(body_cfg.endnode.parents)    # node before end node

        delete_edge!(body_cfg.startnode, N1)
        delete_edge!(N2, body_cfg.endnode)

        add_edge!(branch_cfgnode, loop_var_cfgnode)
        add_edge!(loop_var_cfgnode, N1)
        add_edge!(N2, branch_cfgnode)
        add_edge!(branch_cfgnode, join_cfgnode)

        # join node should only continue to end
        discard = [child for child in join_cfgnode.children if child.type != END_NODE]
        for child in discard
            delete!(join_cfgnode.children, child)
            delete!(child.parents, join_cfgnode)
        end

    elseif is_supported_expression(node) || kind(node) in (K"using", K"import")
        cfgnode = CFGNode(node_id, node, EXPR_NODE)
        push!(nodes, cfgnode)
        add_edge!(startnode, cfgnode)
        add_edge!(cfgnode, endnode)

    elseif kind(node) == K"struct"
        # we do not support structs, but we do not throw error
        add_edge!(startnode, endnode) # skip
    else
        error("Unsupported node kind $node_kind")
    end

    cfg = CFG(startnode, nodes, endnode)
    if node_kind == K"toplevel"
        cfgbuilder.cfgs[node] = cfg
    end
    return cfg
end

function block!(node::CFGNode)
    node.is_blocked = true
end
function unblock!(node::CFGNode)
    node.is_blocked = false
end
function block_joinnode_for_branchnode!(cfg::CFG, branchnode::CFGNode)
    @assert branchnode.type == BRANCH_NODE
    for node in cfg.nodes
        if node.type == JOIN_NODE && node.syntaxnode == branchnode.syntaxnode
            block!(node)
        end
    end
end
function unblock_joinnode_for_branchnode!(cfg::CFG, branchnode::CFGNode)
    @assert branchnode.type == BRANCH_NODE
    for node in cfg.nodes
        if node.type == JOIN_NODE && node.syntaxnode == branchnode.syntaxnode
            unblock!(node)
        end
    end
end

function get_cfgs(scoped_tree::ScopedTree)
    cfgbuilder = CFGBuilder(scoped_tree, Dict())
    get_cfg(cfgbuilder, scoped_tree.root_node, nothing, nothing)
    return Dict(
        (kind(syntaxnode) == K"toplevel" ? :toplevel : get_function_name(syntaxnode)) => cfg
        for (syntaxnode, cfg) in cfgbuilder.cfgs
    )
end

struct CFGRepresentation
    scoped_tree::ScopedTree
    cfgs::Dict{SyntaxNode, CFG} # toplevel -> CFG, functiondef -> CFG
end

function get_cfg_representation(scoped_tree::ScopedTree)
    cfgbuilder = CFGBuilder(scoped_tree, Dict())
    get_cfg(cfgbuilder, scoped_tree.root_node, nothing, nothing)
    @assert all(verify_cfg(cfg) for (_, cfg) in cfgbuilder.cfgs)
    return CFGRepresentation(scoped_tree, cfgbuilder.cfgs)
end

function get_cfg_edges(cfg::CFG)
    edges = Pair{CFGNode,CFGNode}[]
    for node in vcat(cfg.startnode, collect(cfg.nodes), cfg.endnode)
        for child in node.children
            push!(edges, node => child)
        end
    end
    return edges
end

function print_cfg_dot(cfg::CFG)
    println("digraph CFG {")
    println("node [shape=box];")

    for (node, child) in get_cfg_edges(cfg)
        println("\"$node\" -> \"$child\"")
    end
    println("}")    
end


function get_cfgnode_for_syntaxnode(cfg_progr_repr::CFGRepresentation, syntaxnode::SyntaxNode)
    for (_, cfg) in cfg_progr_repr.cfgs, cfgnode in cfg.nodes
        if (cfgnode.type in (ASSIGN_NODE, BRANCH_NODE, RETURN_NODE, EXPR_NODE)) && isdescendant(cfgnode.syntaxnode, syntaxnode)
            return cfg, cfgnode
        end
    end
    error("No CFGNode found for syntaxnode $syntaxnode")
end
function get_cfg_for_function_syntaxnode(cfg_progr_repr::CFGRepresentation, syntaxnode::SyntaxNode)
    if !haskey(cfg_progr_repr.cfgs, syntaxnode)
        error("No CFG found for function $syntaxnode")
    end
    return cfg_progr_repr.cfgs[syntaxnode]
end