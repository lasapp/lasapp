

module ServerEndpoints
# begin

    const _SESSION = Dict()

    import JSONRPC
    import UUIDs
    include("server_interface.jl")

    import JuliaSyntax: JuliaSyntax, SyntaxNode, @K_str, children, kind, sourcetext, first_byte, last_byte
    include("ppls/ppls.jl")
    include("ast/ast.jl")
    
    include("analysis/data_control_flow.jl")
    include("analysis/call_graph.jl")
    include("analysis/interval_arithmetic.jl")
    include("analysis/symbolic.jl")

    function to_server_syntax_node(syntaxtree::SyntaxTree, node::SyntaxNode)::ServerInterface.SyntaxNode
        return ServerInterface.SyntaxNode(
            node_id = syntaxtree.node_to_id[node],
            first_byte = first_byte(node)-1, # index from 0,
            last_byte = last_byte(node),
            source_text = string(sourcetext(node))
        )
    end

    function to_server_random_variable(syntaxtree::SyntaxTree, ppl::PPL, var_def::VariableDefinition, is_observed::Bool)::ServerInterface.RandomVariable
        rv_name = get_random_variable_name(ppl, var_def)
        dist_node = get_distribution_node(ppl, var_def)
        dist_name, dist_params = get_distribution(ppl, dist_node)

        return ServerInterface.RandomVariable(
            node = to_server_syntax_node(syntaxtree, var_def.node),
            name = string(rv_name),
            distribution = ServerInterface.Distribution(
                name = dist_name,
                node = to_server_syntax_node(syntaxtree, dist_node),
                params = [ServerInterface.DistributionParam(name=string(k), node=to_server_syntax_node(syntaxtree, v)) for (k,v) in dist_params]
            ),
            is_observed = is_observed
        )
    end

    const PPLs = Dict("turing" => Turing(), "gen" => Gen())

    function get_syntax_tree(file_name::String)::SyntaxTree
        filecontent = get_file_content_as_string(file_name)
        filecontent = replace(filecontent, ";" => "") # fixes multiple toplevel
        return get_syntax_tree_for_str(filecontent)
    end

    function build_ast(connection, file::ServerInterface.File)
        syntaxtree = get_syntax_tree(file.file_name)
        ppl = PPLs[file.ppl]

        # Replace PPL specific syntax with general sample syntax
        # TODO: check for Gen/Turing
        replace_sample_syntax!(ppl, syntaxtree)

        scoped_tree = get_scoped_tree(syntaxtree)
        
        uuid = string(UUIDs.uuid4())
        _SESSION[uuid] = scoped_tree
        return uuid
    end

    function get_model(connection, file::ServerInterface.File)
        syntaxtree = get_syntax_tree(file.file_name)
        ppl = PPLs[file.ppl]

        model = find_model(syntaxtree.root_node, ppl)

        return ServerInterface.Model(name=String(model.name), node=to_server_syntax_node(syntaxtree, model.node))
    end

    function get_guide(connection, file::ServerInterface.File)
        syntaxtree = get_syntax_tree(file.file_name)
        ppl = PPLs[file.ppl]

        model = find_guide(syntaxtree.root_node, ppl)

        return ServerInterface.Model(name=String(model.name), node=to_server_syntax_node(syntaxtree, model.node))
    end

    function get_random_variables(connection, file::ServerInterface.File)
        syntaxtree = get_syntax_tree(file.file_name)
        ppl = PPLs[file.ppl]
        
        variables = find_variables(syntaxtree.root_node, ppl)
        
        response = Vector{ServerInterface.RandomVariable}()
        for v in variables
            rv = to_server_random_variable(syntaxtree, ppl, v, is_observed(ppl, v))
            push!(response, rv)
        end
        return response
    end

    function get_data_dependencies(connection, params::ServerInterface.tree_node_params)
        syntaxnode = params.node
        scoped_tree = _SESSION[params.tree_id]
        node = get_node_for_id(scoped_tree, syntaxnode.node_id)
        data_deps = data_deps_for_node(scoped_tree, node)

        response = Vector{ServerInterface.SyntaxNode}()
        for dep in data_deps
            push!(response, to_server_syntax_node(scoped_tree.syntaxtree, dep.node))
        end

        return response
    end


    function get_control_parents(connection, params::ServerInterface.tree_node_params)
        scoped_tree = _SESSION[params.tree_id]
        node = get_node_for_id(scoped_tree, params.node.node_id)
        control_deps = control_parents_for_node(scoped_tree, node) # while, for, if, elseif

        response = Vector{ServerInterface.ControlNode}()
        for dep in control_deps
            control_subnode = dep[1] # if condition, loop variable etc.              
            
            push!(response,
                ServerInterface.ControlNode(
                    node = to_server_syntax_node(scoped_tree.syntaxtree, dep),
                    kind = string(kind(dep)),
                    control_subnode = to_server_syntax_node(scoped_tree.syntaxtree, control_subnode),
                    body = [to_server_syntax_node(scoped_tree.syntaxtree, child) for child in dep.children[2:end]] # can have 2 bodies for if statement 
                )
            )
        end

        return response
    end

    function estimate_value_range(connection, params::ServerInterface.estimate_value_range_p)
        scoped_tree = _SESSION[params.tree_id]
        assumptions = Dict{Symbol, Interval}()
        for (rv, interval) in params.assumptions
            rv_node = get_node_for_id(scoped_tree, rv.node.node_id)
            parsed_interval = Interval(parse(Float64,interval.low), parse(Float64, interval.high))
            if kind(rv_node) == K"="
                program_variable_symbol = get_assignment_identifier(rv_node).val
                assumptions[program_variable_symbol] = parsed_interval
            elseif kind(rv_node) == K"function"
                program_variable_symbol = get_function_identifier(rv_node).val
                assumptions[program_variable_symbol] = parsed_interval
            else
                @warn "Cannot mask node of type $(kind(rv_node))"
            end
        end
        # println("assumptions:")
        # println(assumptions)

        node_to_evaluate = get_node_for_id(scoped_tree, params.expr.node_id)

        res = static_interval_eval(scoped_tree, node_to_evaluate, assumptions)
        # println("Response: ", res)
        return ServerInterface.Interval(string(res.low), string(res.high))
    end

    function get_call_graph(connection, params::ServerInterface.tree_node_params)
        scoped_tree = _SESSION[params.tree_id]
        node = get_node_for_id(scoped_tree, params.node.node_id)

        call_graph = compute_call_graph(scoped_tree, node)

        call_nodes = Vector{ServerInterface.CallGraphNode}()
        for (caller, called) in call_graph
            push!(call_nodes, ServerInterface.CallGraphNode(
                to_server_syntax_node(scoped_tree.syntaxtree, caller),
                [to_server_syntax_node(scoped_tree.syntaxtree, c) for c in called]
            ))
        end

        return call_nodes
    end

    function get_path_conditions(connection, params::ServerInterface.get_path_conditions_p)
        scoped_tree = _SESSION[params.tree_id]
        root = get_node_for_id(scoped_tree, params.root.node_id)
        nodes = [get_node_for_id(scoped_tree, node.node_id) for node in params.nodes]
        node_to_symbol = Dict(
            get_node_for_id(scoped_tree, node.node_id) => TypedSymbol_from_str(sexp.expr) for (node, sexp) in params.assumptions
        )
    
        result = get_path_condition_for_nodes(root, nodes, node_to_symbol)
        patch_conditions = [ServerInterface.SymbolicExpression(path_condition_to_str(result[node])) for node in nodes]
        return patch_conditions
    end

    function get_dispatcher()
        msg_dispatcher = JSONRPC.MsgDispatcher()

        msg_dispatcher[ServerInterface.build_ast_rt] = build_ast
        msg_dispatcher[ServerInterface.get_model_rt] = get_model
        msg_dispatcher[ServerInterface.get_guide_rt] = get_guide
        msg_dispatcher[ServerInterface.get_random_variables_rt] = get_random_variables
        msg_dispatcher[ServerInterface.get_data_dependencies_rt] = get_data_dependencies
        msg_dispatcher[ServerInterface.get_control_parents_rt] = get_control_parents
        msg_dispatcher[ServerInterface.estimate_value_range_rt] = estimate_value_range
        msg_dispatcher[ServerInterface.get_call_graph_rt] = get_call_graph
        msg_dispatcher[ServerInterface.get_path_conditions_rt] = get_path_conditions

        return msg_dispatcher
    end

end