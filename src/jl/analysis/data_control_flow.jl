#=
Assumptions:
- functions are pure: no side effects + same output for same arguments (no closures)
    not outside dependence

- thus, assignments only depend on previous expressions

=#

function get_identifiers_node_depends_on(node::SyntaxNode)::Set{SyntaxNode}
    if JuliaSyntax.is_prec_assignment(node)
        if kind(node) == K"="
            # all symbols on right hand side of = plus potential indexes
            # e.g. x[i] = y + 2 depends on i and y, but not x
            lhs = node[1]
            rhs = node[2]
            identifier = get_identifier(lhs)
            assignment_deps = Set(visit(IdentifierFinder(), lhs)) # for example indices name[i]
            delete!(assignment_deps, identifier) # but not name itself
            target_deps = Set(visit(IdentifierFinder(), rhs))
            return assignment_deps ∪ target_deps
        elseif kind(node) in (K"+=", K"-=", K"*=", K"/=", K"//=", K"|=", K"^=", K"÷=", K"%=", K"<<=", K">>=", K">>>=", K"\=", K"&=", K"$=", K"⊻=")
            return Set(visit(IdentifierFinder(), node))
        else
            error("Unsupported assignment: $(kind(node)).")
        end
    
    elseif kind(node) == K"function"
        return Set{SyntaxNode}()

    elseif kind(node) == K"if" || kind(node) == K"elseif" || kind(node) == K"while" || kind(node) == K"for"
        return Set(visit(IdentifierFinder(), node[1])) # only depends on condition / loop range
    end

    # default: all identifiers in node
    return Set(visit(IdentifierFinder(), node))
end


function is_indexed_assignment(node::SyntaxNode)::Bool
    if kind(node) == K"="
        lhs = node[1]
        return kind(lhs) == K"ref" # x[...] = ...
    end
    return false
end

function ReturnFinder(func::SyntaxNode)::NodeFinder{SyntaxNode}
    @assert kind(func) == K"function"
    return NodeFinder{SyntaxNode}(n -> kind(n) == K"return", visit_predicate=n -> n == func || kind(n) != K"function")
end

function data_deps_for_func(scoped_tree::ScopedTree, node::SyntaxNode)::Set{NameDefinition}
    # get all data dependencies of return statements
    return_finder = ReturnFinder(node)
    data_deps = Set{NameDefinition}()
    return_stmts = visit(return_finder, node)
    for return_stmt in return_stmts
        data_deps = data_deps ∪ data_deps_for_node(scoped_tree, return_stmt)
    end
    return data_deps
end

function data_deps_for_node(scoped_tree::ScopedTree, node::SyntaxNode)::Set{NameDefinition}
    @assert isdescendant(scoped_tree.root_node, node)

    if kind(node) == K"function"
        return data_deps_for_func(scoped_tree, node)
    end

    node_is_while_loop_test = kind(node.parent) == K"while" && node.parent[1] == node

    # find all user defined identifiers in expression
    identifiers = get_identifiers_node_depends_on(node)
    # we only care about user defined symbols
    identifiers = filter(i -> i.val in scoped_tree.all_user_symbols, identifiers)
    # println("identifiers: ", identifiers)

    data_deps = Set{NameDefinition}()
    for identifier in identifiers
        # find scope of identifier
        scope = scoped_tree.node_to_scope[identifier]

        # find all assignments in all scopes `identifier = ...` that occur before expression
        for def in scoped_tree.all_definitions
            # filter for assignments which correspond *exactly* to identifier
            # there can be multiple definitions of same symbol, we only care about those which correspond
            # exactly to identifier (the scope in which they are defined is the same)
            def_scope = scoped_tree.node_to_scope[def.identifier]
            if def_scope == scope && def.name == identifier.val
                # println(i, ", ", def, ": ", def.node.position, " < ", node.position, "?")
                if (def.node.position < node.position) || # guarantees acyclic data dependencies
                    (def.node.position ==  node.position && is_indexed_assignment(node)) # indexed (array) assignments may be cyclic

                    # check if nodes are in mutually exclusive branches
                    if !is_in_different_branch(def.node, node)
                        # expression depends on this assignment
                        push!(data_deps, def)
                    end
                end

                if node_is_while_loop_test
                    # node is test of a while loop, so it may depend on while body
                    if isdescendant(node.parent[2], def.node)
                        push!(data_deps, def)
                    end
                end
            end
        end

        # check if identifier is a user-defined function
        for func in scoped_tree.all_functions
            def_scope = scoped_tree.node_to_scope[func.identifier]
            if def_scope == scope && func.name == identifier.val
                push!(data_deps, func)
                break
            end            
        end
    end
    return data_deps
end

function control_parents_for_func(scoped_tree::ScopedTree, node::SyntaxNode)::Vector{SyntaxNode}
    # get all data dependencies of return statements
    return_finder = ReturnFinder(node)
    control_nodes = Set{SyntaxNode}()
    for return_stmt in visit(return_finder, node)
        for control_parent in control_parents_for_node(scoped_tree, return_stmt)
            push!(control_nodes, control_parent)
        end
    end
    return collect(control_nodes)
end

function control_parents_for_node(scoped_tree::ScopedTree, node::SyntaxNode)::Vector{SyntaxNode}
    @assert isdescendant(scoped_tree.root_node, node)

    if kind(node) == K"function"
        return control_parents_for_func(scoped_tree, node)
    end

    control_nodes = Set{SyntaxNode}()  # have necessarily position < node.position

    nodes_to_analyse = SyntaxNode[node]

    # get encompassing function and find all return statements
    # return statments cause branching in control flow graph
    current_node = node
    parent_function = nothing
    while !isnothing(current_node.parent)
        current_node = current_node.parent
        if kind(current_node) == K"function"
            parent_function = current_node
            break
        end
    end
    if !isnothing(parent_function)
        return_finder = ReturnFinder(parent_function)
        return_statments = [return_stmt for return_stmt in visit(return_finder, parent_function) if return_stmt.position < node.position]
        append!(nodes_to_analyse, return_statments)
    end

    # get all "if, while, for" parents for node and all return statments
    for node in nodes_to_analyse
        current_node = node
        while !isnothing(current_node.parent)
            if kind(current_node) == K"function"
                break
            end
            current_node = current_node.parent
            if (kind(current_node) == K"if" ||
                kind(current_node) == K"elseif" ||
                kind(current_node) == K"while" ||
                kind(current_node) == K"for")

                if node != current_node[1] # if the node is the condition / loop variable itself, then no dependency
                    push!(control_nodes, current_node)
                end
            end
            if kind(current_node) == K"generator"
                if node != current_node[2] # if the node is the condition / loop variable itself, then no dependency
                    push!(control_nodes, current_node)
                end
            end
        end
    end

    return collect(control_nodes)
end
