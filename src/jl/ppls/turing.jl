
struct Turing <: PPL end

function is_model(::Turing, node::SyntaxNode)::Bool
    if (kind(node) == K"macrocall")
        @assert length(node.children) > 1
        @assert kind(node.children[1]) == K"MacroName"
        if node.children[1].data.val == Symbol("@model")
            return true
        end
    end
    return false
end

function get_model_name(::Turing, node::SyntaxNode)::Symbol
    return get_function_name(node[2])
end

# operates on preprocessed syntax

function is_random_variable_definition(::Turing, node::SyntaxNode)::Bool
    if kind(node) == K"=" && kind(node[2]) == K"call"
        callnode = node[2]
        callname = get_call_name(callnode)
        return (callname == :SAMPLE || callname == :OBSERVE)
    end
    return false
end

function get_random_variable_name(ppl::PPL, variable::VariableDefinition)::Symbol
    address_node = get_address_node(ppl, variable)
    @assert kind(address_node) == K"tuple"
    # return Symbol(sourcetext(address_node))

    try
        rv_name = try_unparse(address_node[1])
        if length(address_node.children) > 1
            rv_name *= "[" * join(try_unparse.(address_node.children[2:end]), ",") * "]"
        end
        return Symbol(rv_name)
    catch e
        # fall back
        return Symbol(sourcetext(address_node))
    end
end

function get_address_node(ppl::PPL, variable::VariableDefinition)::SyntaxNode
    callnode = variable.node[2]
    first_arg = callnode[2]
    return first_arg
end

function is_observed(ppl::Turing, variable::VariableDefinition)::Bool
    callnode = variable.node[2]
    callname = get_call_name(callnode)
    return callname == :OBSERVE
end

function get_distribution_node(ppl::Turing, variable::VariableDefinition)::SyntaxNode
    callnode = variable.node[2]
    second_arg = callnode[3]
    return second_arg
end

# parameters follow convention of Wikipedia
function get_distribution(ppl::Turing, distribution_node::SyntaxNode)::Tuple{String, Dict{String,SyntaxNode}}
    if kind(distribution_node) != K"call"
        dist_name = "Unknown"
        dist_params = (distribution=distribution_node,)
        return dist_name, dist_params
    end

    call_name = get_call_name(distribution_node)
    if call_name == :filldist
        # broadcasted distribution, filldist(Normal(0,1), N)
        distribution_node = distribution_node[2]
        name = get_call_name(distribution_node)
    elseif call_name == :truncated
        truncated_dist = distribution_node[2]
        name = get_call_name(truncated_dist)
        if name == :Normal
            name = :TruncatedNormal
            params = copy(truncated_dist.children[2:end])
            truncated_params = distribution_node[3]
            @assert kind(truncated_params) == K"parameters" "Unsupported truncated distribution $distribution_node"
            push!(params, truncated_params)
            return parse_distribution(name, params)
        end
    else
        name = call_name
    end
    
    params = distribution_node.children[2:end]
    return parse_distribution(name, params)
end

function is_observed_turing(node::SyntaxNode)
    target = node.children[1]

    if JuliaSyntax.is_literal(target)
        # e.g. true ~ Bernoulli(0.5)
        return true
    end

    while kind(node) != K"macrocall"
        node = node.parent
    end

    @assert kind(node.children[1]) == K"MacroName"
    @assert node.children[1].data.val == Symbol("@model")
    func = node.children[2]
    model_parameters = get_parameter_names_of_function(func)

    varname = get_identifier_of_assignment_target(target).val
    return varname in model_parameters
end

mutable struct TuringPreprocessor <: NodeTransformer
    syntaxtree::SyntaxTree
    function TuringPreprocessor(syntaxtree::SyntaxTree)
        return new(syntaxtree)
    end
end

function visit!(visitor::TuringPreprocessor, node::SyntaxNode)::Union{Nothing,SyntaxNode}
    syntaxtree = visitor.syntaxtree
    
    if kind(node) == K"macrocall" && node[1].val == Symbol("@.") && kind(node[2,2]) == K"~"
        # @. x ~ dist -> x ~ dist
        replace_node = node[2]
        parent = node.parent
        ix = delete_child!(node.parent, node)
        insert_child!(parent, ix, replace_node)
        node = replace_node
    end

    if (
        (kind(node) == K"call" || kind(node) == K"dotcall") &&
        length(children(node)) == 3 &&
        kind(node.children[2]) == K"~"
        )
        # is random variable definition

        @assert kind(node.parent) in JuliaSyntax.KSet"block return" "Sample statement $node is not direct child of block node ($(kind(node.parent)))!"

        address_node = node.children[1]
        dist_node = node.children[3]

        if JuliaSyntax.is_literal(address_node)
            # e.g. true ~ Bernoulli(0.5)
            pv_node = get_empty_syntax_node(K"Identifier", val=:_)
            add_node!(syntaxtree, pv_node)
        else
            pv_node = address_node
        end

        is_obs = is_observed_turing(node)

        # make sure we can reference pv_node, dist_node (and obs_node) with their range
        assignment_node = get_empty_syntax_node(K"=", position=node.position, span=node.raw.span, source=node.source)
        call_node = get_empty_syntax_node(K"call", position=node.position, span=node.raw.span)
        call_name = get_empty_syntax_node(K"Identifier", val=is_obs ? :OBSERVE : :SAMPLE, position=node.position, span=UInt32(0))
        # tuple node inherits source text from address node
        tuple_node = get_empty_syntax_node(K"tuple", flags=JuliaSyntax.PARENS_FLAG, position=address_node.position, span=address_node.raw.span, source=node.source)

        assignment_node.parent = node.parent
        set_children!(assignment_node, SyntaxNode[pv_node, call_node])

        if JuliaSyntax.is_literal(address_node)
            # empty name node
            set_children!(tuple_node, SyntaxNode[])
        elseif kind(address_node) == K"Identifier"
            string_node = get_empty_syntax_node(K"String", val=string(address_node.val))
            add_node!(syntaxtree, string_node)
            set_children!(tuple_node, SyntaxNode[string_node])
        elseif kind(address_node) == K"ref" && kind(address_node[1]) == K"Identifier"
            string_node = get_empty_syntax_node(K"String", val=string(address_node[1].val))
            add_node!(syntaxtree, string_node)
            tuple_node_children = SyntaxNode[string_node]
            for child in JuliaSyntax.children(address_node)[2:end]
                push!(tuple_node_children, copy_node_and_add_to_syntaxtree!(syntaxtree, child))
            end
            set_children!(tuple_node, tuple_node_children)
        else
            error("Unknown address node $address_node")
        end

        set_children!(call_node, SyntaxNode[call_name, tuple_node, dist_node])


        id = visitor.syntaxtree.node_to_id[node]
        syntaxtree.id_to_node[id] = assignment_node
        syntaxtree.node_to_id[assignment_node] = id

        add_node!(syntaxtree, call_node)
        add_node!(syntaxtree, call_name)
        add_node!(syntaxtree, tuple_node)
        
        return assignment_node
    end

    if kind(node) == K"return"
        node = generic_visit!(visitor, node)
        if is_random_variable_definition(Turing(), node[1])
            rv = node[1]
            # handle return x ~ dist, as in Turing turials
            # replace with x ~ dist
            @assert kind(node.parent) == K"block"
            block = node.parent
            ix = delete_child!(block, node)
            insert_child!(block, ix, rv)
            return rv
        end
        return node
    end

    return generic_visit!(visitor, node)
end


function preprocess_syntaxtree!(ppl::Turing, syntax_tree::SyntaxTree)
    visit!(DistributionPreprocessor(syntax_tree), syntax_tree.root_node)
    visit!(TuringPreprocessor(syntax_tree), syntax_tree.root_node)
end


# include("distributions.jl")

# s = """
# @model function m(a, b)
#     x ~ Normal()
#     y[i] ~ Normal(0,1)
#     true ~ Bernoulli(0.5)
#     a ~ Normal(0,1)
#     b[i] ~ Normal(0,1)
# end
# """

# st = get_syntax_tree_for_str(s);
# st.root_node
# preprocess_syntaxtree!(Turing(), st)


# s = """
# @model function m(a, b)
#     return x ~ Normal()
# end
# """

# st = get_syntax_tree_for_str(s);
# st.root_node
# preprocess_syntaxtree!(Turing(), st)