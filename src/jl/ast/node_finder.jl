
# traverses syntax tree
# for all nodes that satisify predicate, the function map is applied and the result is stored
# if visit_matched_nodes is set to true, then also children of nodes that satisify predicate are traversed

struct NodeFinder{T} <: NodeVisitor where T
    predicate::Function # SyntaxNode -> Bool
    map::Function # SyntaxNode -> T
    result::Vector{T}
    visit_predicate::Function # SyntaxNode -> Bool
    function NodeFinder{T}(predicate::Function, map::Function=identity; visit_matched_nodes=false, visit_predicate::Union{Nothing,Function}=nothing) where T
        if isnothing(visit_predicate)
            if visit_matched_nodes
                visit_predicate = _ -> true
            else
                visit_predicate = node -> !predicate(node)
            end
        end
        return new{T}(predicate, map, T[], visit_predicate)
    end
end

function visit(visitor::NodeFinder, node::SyntaxNode)
    if visitor.predicate(node)
        push!(visitor.result, visitor.map(node))
    end
    if visitor.visit_predicate(node)
        generic_visit(visitor, node)
    end
    return visitor.result
end

ModelFinder(ppl::PPL, name::Symbol) = NodeFinder{Model}(
    node -> is_model(ppl, node) && get_model_name(ppl, node) == name,
    node -> Model(name, node)
)

function find_model_or_guide(syntaxtree::SyntaxNode, ppl::PPL, keyword::Symbol)
    @assert kind(syntaxtree) == K"toplevel"
    # find global variable model = ..., guide = ... specifying model/guide name
    model_name = Symbol("")
    for child in children(syntaxtree)
        if kind(child) == K"=" && kind(child[1]) == K"Identifier" && child[1].val == keyword
            if kind(child[2]) == K"call"
                model_name = get_call_name(child[2])
                break
            end
            if kind(child[2]) == K"Identifier"
                model_name = child[2].val
                break
            end
        end
    end
    if model_name == Symbol("")
        @warn "$(titlecase(String(keyword))) name not found. Defaulting to '$keyword'"
        model_name = keyword
    end

    # find node that satisifies is_model(node) and get_model_name(node) == model_name
    model_finder = ModelFinder(ppl, model_name)
    visit(model_finder, syntaxtree)
    @assert length(model_finder.result) > 0 "No $(String(keyword)) definition found."
    @assert length(model_finder.result) == 1 "Multiple $(String(keyword)) definition found."
    return model_finder.result[1]
end

function find_model(syntaxtree::SyntaxNode, ppl::PPL)
    return find_model_or_guide(syntaxtree, ppl, :model)
end

function find_guide(syntaxtree::SyntaxNode, ppl::PPL)
    return find_model_or_guide(syntaxtree, ppl, :guide)
end

VariableDefinitionCollector(ppl::PPL) = NodeFinder{VariableDefinition}(
    node -> is_random_variable_definition(ppl, node),
    node -> VariableDefinition(node)
)

function find_variables(node::SyntaxNode, ppl::PPL)
    variable_collector = VariableDefinitionCollector(ppl)
    visit(variable_collector, node)

    return variable_collector.result
end

IdentifierFinder() = NodeFinder{SyntaxNode}(node -> is_variable_identifier(node), node -> node) # returns identifier
IdentifierSymbolFinder() = NodeFinder{Symbol}(node -> is_variable_identifier(node), node -> node.val) # returns symbols
