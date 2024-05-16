
abstract type PPL end

struct VariableDefinition
    node::SyntaxNode
end

struct Model
    name::Symbol
    node::SyntaxNode
end

function is_model(::PPL, node::SyntaxNode)::Bool
    error("Not implemented.")
end

function get_model_name(::PPL, node::SyntaxNode)::Symbol
    error("Not implemented.")
end

function is_random_variable_definition(::PPL, node::SyntaxNode)::Bool
    error("Not implemented.")
end

function get_random_variable_name(ppl::PPL, variable::VariableDefinition)::Symbol
    error("Not implemented.")
end

function get_address_node(ppl::PPL, variable::VariableDefinition)::SyntaxNode
    error("Not implemented.")
end

function is_observed(ppl::PPL, variable::VariableDefinition)::Bool
    error("Not implemented.")
end

function get_distribution_node(ppl::PPL, variable::VariableDefinition)::SyntaxNode
    error("Not implemented.")
end

# parameters follow convention of Wikipedia
# returns distribution name + map of paramter name to syntax node
function get_distribution(ppl::PPL, distribution_node::SyntaxNode)::Tuple{String, Dict{String,SyntaxNode}}
    error("Not implemented.")
end

function preprocess_syntaxtree!(ppl::PPL, syntax_tree::SyntaxTree)
    error("Not implemented.")
end