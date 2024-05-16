
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

IdentifierFinder() = NodeFinder{SyntaxNode}(node -> is_variable_identifier(node), node -> node) # returns identifier
IdentifierSymbolFinder() = NodeFinder{Symbol}(node -> is_variable_identifier(node), node -> node.val) # returns symbols
