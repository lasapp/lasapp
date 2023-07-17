

struct NodeIdentifier <: NodeVisitor
    node_to_id::Dict{SyntaxNode, String}
    id_to_node::Dict{String, SyntaxNode}
    function NodeIdentifier()
        return new(Dict(), Dict())
    end
end

function visit(visitor::NodeIdentifier, node::SyntaxNode)
    id = "node_$(length(visitor.id_to_node))"
    visitor.id_to_node[id] = node
    visitor.node_to_id[node] = id
    generic_visit(visitor, node)
end

struct SyntaxTree
    root_node::SyntaxNode
    node_to_id::Dict{SyntaxNode, String}
    id_to_node::Dict{String, SyntaxNode}
end

function get_syntax_tree_for_str(s::String)::SyntaxTree
    root_node = JuliaSyntax.parseall(SyntaxNode, s)
    node_identifier = NodeIdentifier()
    visit(node_identifier, root_node)
    return SyntaxTree(root_node, node_identifier.node_to_id, node_identifier.id_to_node)
end