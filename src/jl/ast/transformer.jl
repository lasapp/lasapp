import JuliaSyntax: SyntaxNode, children, SyntaxData, GreenNode, SyntaxHead, EMPTY_FLAGS, SourceFile, Kind

abstract type NodeTransformer end

# Result is in general abstract syntax tree instead of concrete syntax tree (SyntaxNodes with correspoinding GreenNodes).
# You have to know for which nodes of the resulting tree you care about the position in the source.
function generic_visit!(visitor::NodeTransformer, node::SyntaxNode)::SyntaxNode
    i = 0
    for child in children(node)
        new_child = visit!(visitor, child)
        if !isnothing(new_child)
            i += 1
            node.children[i] = new_child
        end
    end
    if !isnothing(node.children)
        resize!(node.children, i)
    end

    return node
end

function visit!(visitor::NodeTransformer, node::SyntaxNode)::Union{Nothing,SyntaxNode}
    return generic_visit!(visitor, node)
end

function set_children!(node::SyntaxNode, children::Union{Nothing,Vector{SyntaxNode}})
    node.children = children
    for child in children
        child.parent = node
    end
end
