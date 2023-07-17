

module ServerInterface
    abstract type MethodParams end

    import JSONRPC

    # JSONRPC.@dict_readable macro creates StructName(d::Dict) abd StructName(;field::type,...) constructors
    # make automatic conversion possible by calling this constructor
    Base.convert(::Type{T}, d::Dict) where T <: JSONRPC.Outbound = T(d)
    Base.convert(::Type{T}, d::Dict) where T <: MethodParams = T(d)

    # request and response types

    JSONRPC.@dict_readable struct SyntaxNode <: JSONRPC.Outbound
        node_id::String
        first_byte::Int
        last_byte::Int
        source_text::String
    end

    JSONRPC.@dict_readable struct ControlNode <: JSONRPC.Outbound
        node::SyntaxNode
        kind::String
        control_subnode::SyntaxNode
        body::Vector{SyntaxNode}
    end

    JSONRPC.@dict_readable struct CallGraphNode <: JSONRPC.Outbound
        caller::SyntaxNode
        called::Vector{SyntaxNode}
    end


    JSONRPC.@dict_readable struct Model <: JSONRPC.Outbound
        name::String
        node::SyntaxNode
    end

    JSONRPC.@dict_readable struct DistributionParam <: JSONRPC.Outbound
        name::String
        node::SyntaxNode
    end

    JSONRPC.@dict_readable struct Distribution <: JSONRPC.Outbound
        name::String
        node::SyntaxNode
        params::Vector{DistributionParam}
    end

    JSONRPC.@dict_readable struct RandomVariable <: JSONRPC.Outbound
        node::SyntaxNode
        name::String
        distribution::Distribution
        is_observed::Bool
    end

    JSONRPC.@dict_readable struct File <: JSONRPC.Outbound
        file_name::String
        ppl::String
    end

    JSONRPC.@dict_readable struct Interval <: JSONRPC.Outbound
        low::String # to allow inf
        high::String
    end

    JSONRPC.@dict_readable struct SymbolicExpression <: JSONRPC.Outbound
        expr::String
    end

    # endpoints

    const build_ast_rt = JSONRPC.RequestType("build_ast", File, String)

    const get_model_rt = JSONRPC.RequestType("get_model", File, Model)
    
    const get_guide_rt = JSONRPC.RequestType("get_guide", File, Model)

    const get_random_variables_rt = JSONRPC.RequestType("get_random_variables", File, Vector{RandomVariable})

    JSONRPC.@dict_readable struct tree_node_params <: MethodParams
        tree_id::String
        node::SyntaxNode
    end

    const get_data_dependencies_rt = JSONRPC.RequestType("get_data_dependencies", tree_node_params, Vector{SyntaxNode})

    const get_control_parents_rt = JSONRPC.RequestType("get_control_parents", tree_node_params, Vector{ControlNode})

    JSONRPC.@dict_readable struct estimate_value_range_p <: MethodParams
        tree_id::String
        expr::SyntaxNode
        assumptions::Vector{Tuple{RandomVariable,Interval}}
    end
    const estimate_value_range_rt = JSONRPC.RequestType("estimate_value_range", estimate_value_range_p, Interval)

    const get_call_graph_rt = JSONRPC.RequestType("get_call_graph", tree_node_params, Vector{CallGraphNode})

    JSONRPC.@dict_readable struct get_path_conditions_p <: MethodParams
        tree_id::String
        root::SyntaxNode
        nodes::Vector{SyntaxNode}
        assumptions::Vector{Tuple{SyntaxNode,SymbolicExpression}}
    end
    const get_path_conditions_rt = JSONRPC.RequestType("get_path_conditions", get_path_conditions_p, Vector{SymbolicExpression})

end