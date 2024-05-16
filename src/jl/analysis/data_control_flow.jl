
function get_assignnode_target(cfgnode::CFGNode)
    @assert cfgnode.type == ASSIGN_NODE
    return get_assignnode_target(cfgnode.syntaxnode)
end

function get_assignnode_target(syntaxnode::SyntaxNode)::SyntaxNode
    @assert JuliaSyntax.is_prec_assignment(kind(syntaxnode))
    lhs = syntaxnode[1]
    if kind(lhs) == K"tuple"
        error("Tuple assignemnts not supported: $syntaxnode")
    else
        return get_identifier_of_assignment_target(lhs)
    end
end

function is_referenced_identifier(identifier::SyntaxNode)
    # does not support arbitrary referenced identifier (like Main.x[...], obj.x[...]) yet
    return kind(identifier) == K"Identifier" && kind(identifier.parent) == K"ref" # x[...]
end
function peval_ints(node::SyntaxNode)
    if kind(node) == K"Integer"
        return node.val
    end
    if kind(node) == K"call"
        # only supported ops yet
        if kind(node[2]) == K"+"
            return peval_ints(node[1]) + peval_ints(node[3])
        elseif kind(node[2]) == K"-"
            return peval_ints(node[1]) - peval_ints(node[3])
        end
    end
    return NaN
end
function get_static_index_of_ref_identifier(identifier::SyntaxNode)
    ref_node = identifier.parent
    if kind(ref_node) != K"ref"
        return NaN
    end
    index_nodes = ref_node.children[2:end]
    return [peval_ints(index_node) for index_node in index_nodes]
end
# only applicable for container variables
function point_to_same_element(identifier1::SyntaxNode, identifier2::SyntaxNode)
    if !(is_referenced_identifier(identifier1) && is_referenced_identifier(identifier2))
        return false
    end
    return get_static_index_of_ref_identifier(identifier1) == get_static_index_of_ref_identifier(identifier2)
end

# returns ASSIGN_NODE and FUNCARG_NODE
function get_RDs!(scoped_tree::ScopedTree, cfgnode::CFGNode, identifier::SyntaxNode, path::Vector{CFGNode}, rds::Set{CFGNode})::Set{CFGNode}
    for parent in cfgnode.parents
        if parent.type == ASSIGN_NODE
            target = get_assignnode_target(parent)
            if identifieres_are_the_same(scoped_tree, identifier, target)
                # matching identifier
                push!(rds, parent)
                if !(is_referenced_identifier(target))
                    continue
                end
                if point_to_same_element(identifier, target)
                    continue
                end
            end
        elseif parent.type == FUNCARG_NODE
            if identifieres_are_the_same(scoped_tree, identifier, get_parameter_identifier(parent.syntaxnode))
                # matching identifier
                push!(rds, parent)
                continue
            end
        end
        is_cycle = any(p == parent for p in path)
        if !is_cycle
            # can avoid copy if we do not branch paths
            new_path = length(cfgnode.parents) > 1 ? copy(path) : path
            push!(new_path, parent)
            get_RDs!(scoped_tree, parent, identifier, new_path, rds) # continue exploring path
        end
    end
    return rds
end

get_RDs(scoped_tree::ScopedTree, cfgnode::CFGNode, identifier::SyntaxNode) = get_RDs!(scoped_tree, cfgnode, identifier, Vector{CFGNode}(), Set{CFGNode}())

function get_BPs!(scoped_tree::ScopedTree, cfgnode::CFGNode, path::Vector{CFGNode}, bps::Set{CFGNode})
    for parent in cfgnode.parents
        if parent.type == BRANCH_NODE
            is_closed = any(p.syntaxnode == parent.syntaxnode for p in path if p.type == JOIN_NODE)
            # if branch node is parent of cfgnode there has to be path from cfgnode to corresponding join node
            # except if cfgnode is a return node and skips to join node of function
            if !is_closed
                # B -> ... -> node -> ... -> J
                push!(bps, parent)
            end # otherwise B -> ... -> J -> ... -> node
        end
        is_cycle = any(p == parent for p in path)
        if !is_cycle
            # can avoid copy if we do not branch paths
            new_path = length(cfgnode.parents) > 1 ? copy(path) : path
            push!(new_path, parent)
            get_BPs!(scoped_tree, parent, new_path, bps) # continue exploring path
        end
    end
    return bps
end

get_BPs(scoped_tree::ScopedTree, cfgnode::CFGNode) = get_BPs!(scoped_tree, cfgnode, Vector{CFGNode}(), Set{CFGNode}())

function get_identifiers_read_in_syntaxnode(scoped_tree::ScopedTree, node::SyntaxNode)::Set{SyntaxNode}
    local identifiers::Set{SyntaxNode}
    if JuliaSyntax.is_prec_assignment(node)
        if kind(node) == K"="
            # all symbols on right hand side of = plus potential indexes
            # e.g. x[i] = y + 2 depends on i and y, but not x
            lhs = node[1]
            rhs = node[2]
            target = get_assignnode_target(node)
            assignment_deps = Set(visit(IdentifierFinder(), lhs)) # for example indices name[i]
            assignment_deps = delete!(assignment_deps, target) # but not names itself
            rhs_deps = Set(visit(IdentifierFinder(), rhs))
            identifiers = assignment_deps ∪ rhs_deps

        elseif kind(node) in (K"+=", K"-=", K"*=", K"/=", K"//=", K"|=", K"^=", K"÷=", K"%=", K"<<=", K">>=", K">>>=", K"\=", K"&=", K"$=", K"⊻=")
            # also symbol on the left, e.g. x += y + 2 depends on x and y
            identifiers = Set(visit(IdentifierFinder(), node))

        else
            error("Unsupported assignment: $(kind(node)).")
        end
    elseif is_supported_expression(node)# kind(node) == K"call"
        # function identifiers are included
        identifiers = Set(visit(IdentifierFinder(), node))
    else
        # default: all identifiers in node
        # identifiers = Set(visit(IdentifierFinder(), node))
        println(node)
        error("Unsupported syntaxnode: $(kind(node)).")
    end

    # we only care about user defined symbols
    identifiers = filter(i -> i.val in scoped_tree.all_user_symbols, identifiers)

    return identifiers
    
    

    # elseif kind(node) == K"if" || kind(node) == K"elseif" || kind(node) == K"while" || kind(node) == K"for"
    #     return Set(visit(IdentifierFinder(), node[1])) # only depends on condition / loop range
    # end

end

function find_call_sites_for_function(scoped_tree::ScopedTree, func::SyntaxNode)
    @assert kind(func) == K"function"
    func_identifier = get_function_identifier(func)
    call_finder = NodeFinder{SyntaxNode}(
        node -> (
            (kind(node) == K"call" || kind(node) == K"dotcall") &&
            !is_function_signature(node) &&
            identifieres_are_the_same(scoped_tree, func_identifier, get_call_identifier(node))
         ),
        node -> node)
    visit(call_finder, scoped_tree.root_node)
    return call_finder.result
end

function get_matching_call_arg(param_node::SyntaxNode, call_site::SyntaxNode, func_parameters::Vector{SyntaxNode})
    @assert kind(call_site) == K"call" || kind(call_site) == K"dotcall"
    param_identifier = get_parameter_identifier(param_node)
    call_args = get_call_args(call_site)

    if is_keyword_parameter(param_node)
        matching_call_arg_ix = findfirst(ca -> kind(ca) == K"=" && ca[1].val == param_identifier.val, call_args)
        if !isnothing(matching_call_arg_ix)
            return call_args[matching_call_arg_ix]
        else
            # has to have default arg, we do not check
            return nothing
        end
    else
        # get position of param in function signature
        param_ix = findfirst(p -> get_parameter_identifier(p).val == param_identifier.val, func_parameters)
        @assert !isnothing(param_ix)
        # select param_ix-th argument in call site
        if length(call_args) ≥ param_ix && kind(call_args[param_ix]) != K"="
            return call_args[param_ix]
        else
            # has to have default arg, we do not check
            return nothing
        end
    end
end

function get_all_exprs_passed_to_function_at_param(scoped_tree::ScopedTree, param_node::SyntaxNode)
    exprs = Vector{SyntaxNode}()
    func_syntaxnode = get_function_for_parameter(param_node)
    func_parameters = get_parameter_nodes_of_function(func_syntaxnode)
    # in a pre-processing step we could duplicate the function for each of its calls
    # to make the following more precise, i.e. only <=1 call site per function
    call_sites = find_call_sites_for_function(scoped_tree, func_syntaxnode)
    for call_site in call_sites
        matching_call_arg = get_matching_call_arg(param_node, call_site, func_parameters)
        if !isnothing(matching_call_arg)
            push!(exprs, matching_call_arg)
        end
    end
    return exprs
end
function get_all_exprs_passed_to_function(scoped_tree::ScopedTree, func_syntaxnode::SyntaxNode)
    exprs = Vector{SyntaxNode}()
    call_sites = find_call_sites_for_function(scoped_tree, func_syntaxnode)
    for call_site in call_sites
        call_args = get_call_args(call_site)
        for call_arg in call_args
            push!(exprs, call_arg)
        end
    end
    return exprs
end

function data_deps_for_syntaxnode(cfg_progr_repr::CFGRepresentation, syntaxnode::SyntaxNode)::Set{SyntaxNode}
    if kind(syntaxnode) == K"function"
        # union over data dependencies of all return statements
        cfg = get_cfg_for_function_syntaxnode(cfg_progr_repr, syntaxnode)
        data_deps = Set{SyntaxNode}()
        for cfgnode in cfg.nodes
            if cfgnode.type == RETURN_NODE
                data_deps = data_deps ∪ data_deps_for_syntaxnode(cfg_progr_repr.scoped_tree, cfgnode, get_return_expr(cfgnode))
            end
        end
        return data_deps

    elseif is_parameter_of_function(syntaxnode)
        # union of expression corresponding to parameter in all calls
        data_deps = Set{SyntaxNode}()
        for expr in get_all_exprs_passed_to_function_at_param(cfg_progr_repr.scoped_tree, syntaxnode)
            _, cfgnode = get_cfgnode_for_syntaxnode(cfg_progr_repr, expr)
            data_deps = data_deps ∪ data_deps_for_syntaxnode(cfg_progr_repr.scoped_tree, cfgnode, expr)
        end
        return data_deps

    elseif is_function_signature(syntaxnode)
        # union of expression corresponding to ALL parameters in all calls
        data_deps = Set{SyntaxNode}()
        func_syntaxnode = get_function_for_signature_node(syntaxnode)
        for expr in get_all_exprs_passed_to_function(cfg_progr_repr.scoped_tree, func_syntaxnode)
            _, cfgnode = get_cfgnode_for_syntaxnode(cfg_progr_repr, expr)
            data_deps = data_deps ∪ data_deps_for_syntaxnode(cfg_progr_repr.scoped_tree, cfgnode, expr)
        end
        return data_deps

    else
        # normal case
        _, cfgnode = get_cfgnode_for_syntaxnode(cfg_progr_repr, syntaxnode)
        return data_deps_for_syntaxnode(cfg_progr_repr.scoped_tree, cfgnode, syntaxnode)
    end
end

function data_deps_for_syntaxnode(scoped_tree::ScopedTree, cfgnode::CFGNode, syntaxnode::SyntaxNode)::Set{SyntaxNode}
    identifiers = get_identifiers_read_in_syntaxnode(scoped_tree, syntaxnode)

    data_deps = Set{SyntaxNode}()
    for identifier in identifiers
        # check if identifier is a user-defined function
        ix = findfirst(func -> identifieres_are_the_same(scoped_tree, identifier, func.identifier), scoped_tree.all_functions)
        if !isnothing(ix)
            # identifier is function
            func = scoped_tree.all_functions[ix]
            push!(data_deps, func.node)
        else
            # identifier is program variable
            rds = get_RDs(scoped_tree, cfgnode, identifier)
            for rd in rds
                push!(data_deps, rd.syntaxnode)
            end
        end
    end

    return data_deps
end

# returns true if startnode is reachable from endnode
function is_reachable!(startnode::CFGNode, endnode::CFGNode, path::Vector{CFGNode})
    if endnode.is_blocked
        return false
    end
    for parent in endnode.parents
        if parent == startnode
            return true
        end
        is_cycle = any(p == parent for p in path)
        if !is_cycle
            new_path = length(endnode.parents) > 1 ? copy(path) : path
            push!(new_path, parent)
            if is_reachable!(startnode, parent, new_path)
                return true
            end
        end
    end
    return false
end
function is_reachable(startnode::CFGNode, endnode::CFGNode)
    return is_reachable!(startnode, endnode, CFGNode[])
end

function is_on_path_between_nodes(node::CFGNode, startnode::CFGNode, endnode::CFGNode)
    return is_reachable(startnode, node) && is_reachable(node, endnode)
end

function control_parents_for_syntaxnode(cfg_progr_repr::CFGRepresentation, syntaxnode::SyntaxNode)::Set{SyntaxNode}
    if kind(syntaxnode) == K"function"
        cfg = get_cfg_for_function_syntaxnode(cfg_progr_repr, syntaxnode)
        cfgnode = first(cfg.endnode.parents) # function join node
        return control_parents_for_cfgnode(cfg_progr_repr.scoped_tree, cfg, cfgnode)

    elseif is_parameter_of_function(syntaxnode) || is_function_signature(syntaxnode)
        # union of control parents of all function calls
        control_parents = Set{SyntaxNode}()
        func_syntaxnode = is_parameter_of_function(syntaxnode) ? get_function_for_parameter(syntaxnode) : get_function_for_signature_node(syntaxnode)
        call_sites = find_call_sites_for_function(cfg_progr_repr.scoped_tree, func_syntaxnode)
        for call_site in call_sites
            control_parents = control_parents ∪ control_parents_for_syntaxnode(cfg_progr_repr, call_site)
        end
        return control_parents
    else
        # normal case
        cfg, cfgnode = get_cfgnode_for_syntaxnode(cfg_progr_repr, syntaxnode)
        return control_parents_for_cfgnode(cfg_progr_repr.scoped_tree, cfg, cfgnode)
    end
end

function control_parents_for_cfgnode(scoped_tree::ScopedTree, cfg::CFG, cfgnode::CFGNode)::Set{SyntaxNode}
    @assert cfgnode in cfg.nodes
    # branch parent is only the `control_node` TODO: change this and only return control_node?
    bps = get_BPs(scoped_tree, cfgnode)

    # all branch nodes form a branch join pair with the function join node which joins all return nodes
    # the endnode is the only child of the function join node
    if cfg.startnode.type == FUNCSTART_NODE
        for branch_node in cfg.nodes
            branch_node.type != BRANCH_NODE && continue
            if is_on_path_between_nodes(cfgnode, branch_node, cfg.endnode)
                # check if there is a path from branch_node to cfg.endnode
                # that does not go through its join node or through the cfgnode
                # -> the execution of cfgnode truly depends on branchnode
                block!(cfgnode); block_joinnode_for_branchnode!(cfg, branch_node)
                if is_reachable(branch_node, cfg.endnode)
                    push!(bps, branch_node)
                end
                unblock!(cfgnode); unblock_joinnode_for_branchnode!(cfg, branch_node)
            end
        end
    end
    
    return Set{SyntaxNode}(bp.syntaxnode.parent for bp in bps)
end
