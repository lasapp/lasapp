abstract type NodeVisitor end

function generic_visit(visitor::NodeVisitor, node::SyntaxNode)
    for child in children(node)
        visit(visitor, child)
    end
end

function visit(visitor::NodeVisitor, node::SyntaxNode)
    generic_visit(visitor, node)
end