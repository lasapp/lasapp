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

function is_random_variable_definition(::Gen, node::SyntaxNode)::Bool
    if kind(node) == K"=" && kind(node[2]) == K"call" # x = {address} ~ dist
        call_node = node[2]
    elseif kind(node) == K"call" # x ~ dist (== x = {:x} ~ dist)
        call_node = node
    else 
        return false
    end

    return length(children(call_node)) == 3 && kind(call_node.children[2]) == K"~"
end

function get_random_variable_node(::Gen, variable::VariableDefinition)::SyntaxNode
    function get_address(node::SyntaxNode)::SyntaxNode
        @assert kind(node) == K"braces"
        if kind(node[1]) == K"quote"
            return node[1,1]
        else
            return node[1]
        end
    end
    if kind(variable.node) == K"=" # x = {address} ~ dist
        call_node = variable.node[2]
        return get_address(call_node[1])
    else
        if kind(variable.node[1]) == K"braces" # {address} ~ dist
            return get_address(variable.node[1])
        else
            return variable.node[1] # address ~ dist
        end
    end

end
function get_random_variable_name(ppl::Gen, variable::VariableDefinition)::Symbol
    return Symbol(sourcetext(get_random_variable_node(ppl, variable)))
end


function get_program_variable_node(ppl::Gen, variable::VariableDefinition)::SyntaxNode
    if kind(variable.node) == K"="  # x = {address} ~ dist
        return variable.node[1]
    elseif kind(variable.node[1]) == K"braces" # {address} ~ dist
        return get_empty_syntax_node(K"Identifier", val=:_)
    else # address ~ dist
        return get_random_variable_node(ppl, variable)
    end
end

function get_program_variable_name(ppl::Gen, variable::VariableDefinition)::Symbol
    return Symbol(sourcetext(get_random_variable_node(ppl, variable)))
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

function is_observed(ppl::Gen, variable::VariableDefinition)::Bool
    # get to toplevel node
    node = variable.node
    while !isnothing(node.parent)
        node = node.parent
    end
    if kind(node) != K"toplevel"
        return false
    end


    # compare exact sourcetext e.g. :y => i == :y=>i without white spaces
    variable_name = replace(String(get_random_variable_name(ppl, variable)), " "=>"")
    function get_name(node::SyntaxNode)::String
        name_identifier = kind(node) == K"quote" ? node[1] : node
        return replace(sourcetext(name_identifier), " "=>"")
    end
    # println("variable_name: ", variable_name)
    # iteratate over each toplevel assignemnt
    for stmt in children(node)
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
    stmts = visit(node_finder, node)
    # println("variable_name: ", variable_name)
    # println(stmts)
    for stmt in stmts
        if variable_name == get_name(stmt[1,2]) # compare to index
            return true
        end
    end

    return false
end

function get_distribution_node(ppl::Gen, variable::VariableDefinition)::SyntaxNode
    call_node = kind(variable.node) == K"=" ? variable.node[2] : variable.node

    return call_node.children[3]
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

    name = _GEN_DISTRIBUTION_NAMES[gen_name]

    if name == "Exponential"
        parameter_renames = Dict("scale"=>"rate")
    else
        parameter_renames = nothing
    end

    dist_name, dist_params = parse_distribution(name, params; parameter_renames=parameter_renames)

    return dist_name, dist_params
end


