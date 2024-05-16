using JuliaSyntax: sourcetext

struct Gen <: PPL end

function is_model(::Gen, node::SyntaxNode)::Bool
    if (kind(node) == K"macrocall")
        @assert length(node.children) > 1
        @assert kind(node.children[1]) == K"MacroName"
        if node.children[1].data.val == Symbol("@gen")
            return true
        end
    end
    return false
end

function get_model_name(::Gen, node::SyntaxNode)::Symbol
    return get_function_name(node[end])
end

# operates on preprocessed syntax

function is_random_variable_definition(::Gen, node::SyntaxNode)::Bool
    if kind(node) == K"=" && kind(node[2]) == K"call"
        callnode = node[2]
        callname = get_call_name(callnode)
        return (callname == :SAMPLE || callname == :OBSERVE)
    end
    return false
end

function get_random_variable_name(ppl::Gen, variable::VariableDefinition)::Symbol
    address_node = _gen_get_address_node(variable.node)
    return _gen_get_name_from_address_node(address_node)
end

function _gen_get_name_from_address_node(address_node::SyntaxNode)::Symbol
    # no x[...] ~ ...
    local rv_name_str::String
    if kind(address_node) == K"braces"
        try
            rv_name_str = try_unparse(address_node[1])
        catch e
            # fall back
            rv_name_str = sourcetext(address_node[1])
        end
    else
        @assert kind(address_node) == K"quote" # x ~ dist
        rv_name_str = ":$(address_node[1].val)"
    end

    rv_name = Symbol(rv_name_str)
    return rv_name
end


function get_address_node(ppl::Gen, variable::VariableDefinition)::SyntaxNode
    return _gen_get_address_node(variable.node)
end

function _gen_get_address_node(node::SyntaxNode)::SyntaxNode
    callnode = node[2]
    first_arg = callnode[2]
    return first_arg
end

function is_observed(ppl::Gen, variable::VariableDefinition)::Bool
    callnode = variable.node[2]
    callname = get_call_name(callnode)
    return callname == :OBSERVE
end

function get_distribution_node(ppl::Gen, variable::VariableDefinition)::SyntaxNode
    callnode = variable.node[2]
    second_arg = callnode[3]
    return second_arg
end

# gen renames and wraps Distributions.jl
_GEN_DISTRIBUTION_NAMES = Dict(
    :bernoulli => :Bernoulli,
    :beta_uniform => :Unknown,
    :beta => :Beta,
    :binom => :Binomial,
    :categorical => :Categorical,
    :cauchy => :Cauchy,
    :dirichlet => :Dirichlet,
    :exponential => :Exponential,
    :gamma => :Gamma,
    :geometric => :Geometric,
    :inv_gamma => :InverseGamma,
    :laplace => :Laplace,
    :mvnormal => :MvNormal,
    :neg_binom => :NegativeBinomial,
    :normal => :Normal,
    :piecewise_uniform => :Unknown,
    :poisson => :Poisson,
    :uniform_continuous => :Uniform,
    :uniform_discrete => :DiscreteUniform,
)

# parameters follow convention of Wikipedia
function get_distribution(ppl::Gen, distribution_node::SyntaxNode)::Tuple{String, Dict{String,SyntaxNode}}
    if kind(distribution_node) != K"call"
        dist_name = "Unknown"
        dist_params = (distribution=distribution_node,)
        return dist_name, dist_params
    end

    gen_name = get_call_name(distribution_node)
    params = distribution_node.children[2:end]

    name = get(_GEN_DISTRIBUTION_NAMES, gen_name, gen_name)

    if name == "Exponential"
        parameter_renames = Dict("scale"=>"rate")
    else
        parameter_renames = nothing
    end

    dist_name, dist_params = parse_distribution(name, params; parameter_renames=parameter_renames)

    return dist_name, dist_params
end


function preprocess_syntaxtree!(ppl::Gen, syntax_tree::SyntaxTree)
    # no default parameters for Gen
    # visit!(DistributionPreprocessor(syntax_tree), syntax_tree.root_node)
    visit!(TuringPreprocessor(syntax_tree), syntax_tree.root_node)
end


function is_observation_assignment(node::SyntaxNode)
    # observations[...] == ...
    if kind(node) == K"="
        if (kind(node[1]) == K"ref" && kind(node[1,1]) == K"Identifier" && node[1,1].val == :observations)
            current = node.parent
            # only global scope assignemnts
            while !isnothing(current)
                if kind(current) == K"function"
                    return false
                end
                current = current.parent
            end
            return true
        end
    end

    return false
end

function is_observed_gen(toplevel_node::SyntaxNode, address_node::SyntaxNode)
    # compare exact sourcetext e.g. :y => i == :y=>i without white spaces
    variable_name = replace(String(_gen_get_name_from_address_node(address_node)), " "=>"")
    function get_name(node::SyntaxNode)::String
        # name_identifier = kind(node) == K"quote" ? node[1] : node
        return replace(sourcetext(node), " "=>"")
    end
    # println("variable_name: ", variable_name)
    # iteratate over each toplevel assignemnt
    for stmt in children(toplevel_node)
        if kind(stmt) == K"="
            if (kind(stmt[1]) == K"Identifier" && kind(stmt[2]) == K"call" && 
                stmt[2,1].val == :choicemap && stmt[1].val == :observations)
                # observations = choicemap(...)

                # iterate over all (... => ...) arguments to choicemap
                for kv in stmt[2].children[2:end]
                    @assert kind(kv) == K"call" && kind(kv[2]) == K"=>"
                    # println(kv, ": ", get_name(kv[1]))
                    if variable_name == get_name(kv[1]) # left part of =>
                        return true
                    end
                end
            end
        end
    end

    node_finder = NodeFinder{SyntaxNode}(is_observation_assignment)
    stmts = visit(node_finder, toplevel_node)
    # println("variable_name: ", variable_name)
    # println(stmts)
    for stmt in stmts
        # println("stmt: ", get_name(stmt[1,2]))
        if variable_name == get_name(stmt[1,2]) # compare to index
            return true
        end
    end

    return false
end

mutable struct GenPreprocessor <: NodeTransformer
    syntaxtree::SyntaxTree
    function GenPreprocessor(syntaxtree::SyntaxTree)
        return new(syntaxtree)
    end
end

function visit!(visitor::GenPreprocessor, node::SyntaxNode)::Union{Nothing,SyntaxNode}
    syntaxtree = visitor.syntaxtree

    is_rv = false
    local call_node:: SyntaxNode
    local pv_node:: SyntaxNode
    local address_node:: SyntaxNode
    local dist_node:: SyntaxNode
    if ( # x = {address} ~ dist
        kind(node) == K"=" && kind(node[2]) == K"call" &&
        length(children(node[2])) == 3 && kind(node[2,2]) == K"~" &&
        kind(node[2,1]) == K"braces"
        )
        is_rv = true
        pv_node = node[1]
        call_node = node[2]
        address_node = call_node[1]
        dist_node = call_node[3]
    end
    if ( # x ~ dist (== x = {:x} ~ dist)
        kind(node) == K"call"  &&
        kind(node[1]) != K"braces" && 
        length(children(node)) == 3 && kind(node[2]) == K"~"
    )
        is_rv = true
        pv_node = node[1]
        call_node = node
        if kind(pv_node) == K"Identifier"
            quote_node = get_empty_syntax_node(K"quote", flags=JuliaSyntax.COLON_QUOTE, position=node[1].position, span=node[1].raw.span, source=node.source)
            add_node!(syntaxtree, quote_node)
            id_node = get_empty_syntax_node(K"Identifier", val=pv_node.val)
            add_node!(syntaxtree, id_node)

            set_children!(quote_node, SyntaxNode[id_node])
            address_node = quote_node
        # x[i] ~ dist is not allowed
        else
            error("Unknown address node $pv_node")
        end
        address_node = quote_node

        dist_node = call_node[3]
    end
    if ( # {:x} ~ dist (== _ = {:x} ~ dist)
        kind(node) == K"call"  &&
        kind(node[1]) == K"braces" && 
        length(children(node)) == 3 && kind(node[2]) == K"~"
        
        )
        is_rv = true
        call_node = node
        pv_node = get_empty_syntax_node(K"Identifier", val=:_)
        add_node!(syntaxtree, pv_node)
        address_node = call_node[1]
        dist_node = call_node[3]
    end


    if is_rv
        # is random variable definition
        @assert kind(node.parent) == K"block" "Sample statement $node is not direct child of block node!"

         # get to toplevel node
        _node = node
        while !isnothing(_node.parent)
            _node = _node.parent
        end
        @assert kind(_node) == K"toplevel"
  
        is_obs = is_observed_gen(_node, address_node)

        # make sure we can reference pv_node, dist_node (and obs_node) with their range
        assignment_node = get_empty_syntax_node(K"=", position=node.position, span=node.raw.span, source=node.source)
        call_node = get_empty_syntax_node(K"call", position=node.position, span=node.raw.span)
        call_name = get_empty_syntax_node(K"Identifier", val=is_obs ? :OBSERVE : :SAMPLE, position=node.position, span=UInt32(0))

        assignment_node.parent = node.parent
        set_children!(assignment_node, SyntaxNode[pv_node, call_node])
        set_children!(call_node, SyntaxNode[call_name, address_node, dist_node])

        id = visitor.syntaxtree.node_to_id[node]
        syntaxtree.id_to_node[id] = assignment_node
        syntaxtree.node_to_id[assignment_node] = id

        add_node!(syntaxtree, call_node)
        add_node!(syntaxtree, call_name)

        return assignment_node
    end

    return generic_visit!(visitor, node)
end


function preprocess_syntaxtree!(ppl::Gen, syntax_tree::SyntaxTree)
    # visit!(DistributionPreprocessor(syntax_tree), syntax_tree.root_node)
    visit!(GenPreprocessor(syntax_tree), syntax_tree.root_node)
end

include("distributions.jl")

# s = """
# @gen function m()
#     x ~ Normal(0,1)
#     {:y} ~ Normal(0,1)
#     z = {:z} ~ Normal(0,1)
# end
# """

# st = get_syntax_tree_for_str(s);
# st.root_node
# preprocess_syntaxtree!(Gen(), st)



# s = """
# :x
# {:x}
# """
# st = get_syntax_tree_for_str(s);
# n = st.root_node