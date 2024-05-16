

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

function add_node!(syntaxtree::SyntaxTree, node::SyntaxNode)
    id = "node_$(length(syntaxtree.node_to_id))"
    syntaxtree.node_to_id[node] = id
    syntaxtree.id_to_node[id] = node
end
function add_nodes!(syntaxtree::SyntaxTree, nodes...)
    for node in nodes
        add_node!(syntaxtree, node)
    end
end

# removing nodes messes up id = "node_$(length(syntaxtree.node_to_id))" system and is not needed in transformations
# function remove_node!(syntaxtree::SyntaxTree, node::SyntaxNode)
#     id = syntaxtree.node_to_id[node]
#     delete!(syntaxtree.node_to_id, node)
#     delete!(syntaxtree.id_to_node, id)
# end

function get_syntax_tree_for_str(s::String)::SyntaxTree
    root_node = JuliaSyntax.parseall(SyntaxNode, s)
    node_identifier = NodeIdentifier()
    visit(node_identifier, root_node)
    return SyntaxTree(root_node, node_identifier.node_to_id, node_identifier.id_to_node)
end

function copy_node_and_add_to_syntaxtree!(syntaxtree::SyntaxTree, node::SyntaxNode)
    copied_node = SyntaxNode(nothing, nothing, node.data)
    add_node!(syntaxtree, copied_node)
    if JuliaSyntax.haschildren(node)
        copied_node.children = SyntaxNode[]
        for child in JuliaSyntax.children(node)
            copied_child = copy_node_and_add_to_syntaxtree!(syntaxtree, child)
            add_child!(copied_node, copied_child)
        end
    end
    return copied_node
end