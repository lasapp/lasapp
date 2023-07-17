
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

function is_random_variable_definition(::Turing, node::SyntaxNode)::Bool
    return (
        kind(node) == K"call" &&
        length(children(node)) == 3 &&
        kind(node.children[2]) == K"~"
        )
end

function get_random_variable_node(::Turing, variable::VariableDefinition)::SyntaxNode
    return variable.node.children[1]
end
function get_random_variable_name(ppl::Turing, variable::VariableDefinition)::Symbol
    return Symbol(sourcetext(get_random_variable_node(ppl, variable)))
end

function get_program_variable_node(ppl::Turing, variable::VariableDefinition)::SyntaxNode
    return variable.node.children[1]
end

function get_program_variable_name(ppl::Turing, variable::VariableDefinition)::Symbol
    return Symbol(sourcetext(get_random_variable_node(ppl, variable)))
end

function is_observed(ppl::Turing, variable::VariableDefinition)::Bool
    node = variable.node
    while kind(node) != K"macrocall"
        node = node.parent
    end
    @assert kind(node.children[1]) == K"MacroName"
    @assert node.children[1].data.val == Symbol("@model")
    func = node.children[2]
    model_parameters = get_parameters_of_function(func)

    varname = get_identifier(get_random_variable_node(ppl, variable)).val
    return varname in model_parameters
end

function get_distribution_node(ppl::Turing, variable::VariableDefinition)::SyntaxNode
    return variable.node.children[3]
end

# parameters follow convention of Wikipedia
function get_distribution(ppl::Turing, distribution_node::SyntaxNode)::Tuple{String, Dict{String,SyntaxNode}}
    if kind(distribution_node) != K"call"
        dist_name = "Unknown"
        dist_params = (distribution=distribution_node,)
        return dist_name, dist_params
    end

    name = get_call_name(distribution_node)
    params = distribution_node.children[2:end]

    dist_name, dist_params = parse_distribution(name, params)

    return dist_name, dist_params
end