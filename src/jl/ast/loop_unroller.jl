
mutable struct LoopUnroller <: NodeTransformer
    syntaxtree::SyntaxTree
    N::Int
end

function copy_body!(syntaxtree::SyntaxTree, node::SyntaxNode, loop_var::SyntaxNode, loop_var_value::Int)
    if kind(node) == K"Identifier" && node.val == loop_var.val
        replaced_node = get_empty_syntax_node(K"Integer", val=loop_var_value)
        add_node!(syntaxtree, replaced_node)
        return replaced_node
    end
    copied_node = SyntaxNode(nothing, nothing, node.data)
    add_node!(syntaxtree, copied_node)
    if JuliaSyntax.haschildren(node)
        copied_node.children = SyntaxNode[]
        for child in JuliaSyntax.children(node)
            copied_child = copy_body!(syntaxtree, child, loop_var, loop_var_value)
            add_child!(copied_node, copied_child)
        end
    end
    return copied_node
end

function visit!(visitor::LoopUnroller, node::SyntaxNode)::Union{Nothing,SyntaxNode}
    if kind(node) == K"for"
        loop_var_node = node[1]
        @assert kind(loop_var_node) == K"=" "Cannot unroll loop: Unknown loop_var_node $loop_var_node."
        loop_var = loop_var_node[1]
        @assert kind(loop_var) == K"Identifier" "Cannot unroll loop: Unknown loop_var $loop_var."
        loop_range = loop_var_node[2]

        unroll_range = 1:visitor.N
        if kind(loop_range) == K"call" && kind(loop_range[2]) == K":"
            start_node = loop_range[1]
            end_node = loop_range[3]
            if kind(start_node) == K"Integer"
                if kind(end_node) == K"Integer"
                    unroll_range = start_node.val : end_node.val
                else
                    unroll_range = start_node.val : start_node.val + visitor.N - 1
                end
            end
        end
        println("unroll_range: ", unroll_range)
        
        body = node[2]
        @assert kind(body) == K"block"
        node_finder = NodeFinder{SyntaxNode}(node -> kind(node) == K"=" && kind(node[1]) == K"Identifier" && node[1].val == loop_var.val, node -> node)
        visit(node_finder, body)
        @assert length(node_finder.result) == 0 "Cannot unroll loop: Found assignment of loop_var in body: $(node_finder.result)"
        
        block_node = get_empty_syntax_node(K"block")
        block_node.children = SyntaxNode[]
        add_node!(visitor.syntaxtree, block_node)

        parent = node.parent
        ix = delete_child!(parent, node)
        for i in unroll_range
            copied_body = copy_body!(visitor.syntaxtree, body, loop_var, i)
            for child in JuliaSyntax.children(copied_body)
                add_child!(block_node, child)
            end
        end
        insert_child!(parent, ix, block_node)

        # for nested loops
        generic_visit!(visitor, block_node)

        return block_node
    end

    return generic_visit!(visitor, node)
end

function unroll_loops!(syntaxtree::SyntaxTree, N::Int)
    visit!(LoopUnroller(syntaxtree, N), syntaxtree.root_node)
end
# s = """
# for i ∈ 1:10
#     x[i] ~ Normal(i, 1)
# end
# """
# st = get_syntax_tree_for_str(s);
# n = st.root_node

# visit!(LoopUnroller(st, 3), n)
# n
# first_body_copy = n[1,1]
# JuliaSyntax.sourcetext(first_body_copy)


# s = """
# for i ∈ 1:10
#     for j in 1:10
#         x[(i,j)] ~ Normal(i+j, 1)
#     end
# end
# """
# st = get_syntax_tree_for_str(s);
# n = st.root_node

# visit!(LoopUnroller(st, 3), n)

# _show_syntax_node_sexpr(stdout, n)

# first_body_copy = n[1,1]
# JuliaSyntax.sourcetext(first_body_copy)


# i = get_empty_syntax_node(K"Integer", val=1)
# println(i)
