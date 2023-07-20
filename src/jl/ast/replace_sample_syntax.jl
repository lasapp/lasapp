

mutable struct SampleSyntaxReplacer <: NodeTransformer
    ppl::PPL
    syntaxtree::SyntaxTree
    function SampleSyntaxReplacer(ppl::PPL, syntaxtree::SyntaxTree)
        return new(ppl, syntaxtree)
    end
end

#=
replaces
    (call-i name ~ distribution_expr) (Turing)
with
    (= name (call SAMPLE (string "name") distribution_expr))
    (= name (call OBSERVE (string "name") distribution_expr name)))

name and distribution_expr are the original SyntaxNode and have therefore map to GreenNode in source.
=#
function visit!(visitor::SampleSyntaxReplacer, node::SyntaxNode)::Union{Nothing,SyntaxNode}
    if is_random_variable_definition(visitor.ppl, node)
        var_def = VariableDefinition(node)

        rv_name = get_random_variable_name(visitor.ppl, var_def)
        pv_node = get_program_variable_node(visitor.ppl, var_def) # Identifier
        dist_node = get_distribution_node(visitor.ppl, var_def) # Distribution Expression
        # obs_node = get_observed_value_node(visitor.ppl, var_def)

        is_obs = is_observed(visitor.ppl, var_def)

        # make sure we can reference pv_node, dist_node (and obs_node) with their range
        assignment_node = get_empty_syntax_node(K"=", position=node.position, span=node.raw.span, source=node.source)
        call_node = get_empty_syntax_node(K"call", position=node.position, span=node.raw.span)
        call_name = get_empty_syntax_node(K"Identifier", val=is_obs ? :OBSERVE : :SAMPLE, position=node.position, span=UInt32(0))
        name_node = get_empty_syntax_node(K"string", position=node.position, span=UInt32(0))

        assignment_node.parent = node.parent
        set_children!(assignment_node, SyntaxNode[pv_node, call_node])
        string_node = get_empty_syntax_node(K"String", val=string(rv_name))
        set_children!(name_node, SyntaxNode[string_node])

        # if is_obs
        #     set_children!(call_node, SyntaxNode[call_name, name_node, dist_node, obs_node])
        # else
        set_children!(call_node, SyntaxNode[call_name, name_node, dist_node])
        # end

        syntaxtree = visitor.syntaxtree

        id = visitor.syntaxtree.node_to_id[node]
        syntaxtree.id_to_node[id] = assignment_node
        syntaxtree.node_to_id[assignment_node] = id

        id = "node_$(length(syntaxtree.node_to_id))"
        syntaxtree.node_to_id[call_node] = id
        syntaxtree.id_to_node[id] = call_node

        id = "node_$(length(syntaxtree.node_to_id))"
        syntaxtree.node_to_id[call_name] = id
        syntaxtree.id_to_node[id] = call_name

        id = "node_$(length(syntaxtree.node_to_id))"
        syntaxtree.node_to_id[name_node] = id
        syntaxtree.id_to_node[id] = name_node
        
        id = "node_$(length(syntaxtree.node_to_id))"
        syntaxtree.node_to_id[string_node] = id
        syntaxtree.id_to_node[id] = string_node

        return assignment_node
    end
    return generic_visit!(visitor, node)
end


function replace_sample_syntax!(ppl::PPL, syntaxtree::SyntaxTree)
    visit!(SampleSyntaxReplacer(ppl, syntaxtree), syntaxtree.root_node)
end