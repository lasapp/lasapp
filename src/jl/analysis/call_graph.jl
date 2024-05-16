
mutable struct CallFinder <: NodeVisitor
    calls::Vector{SyntaxNode}
    function CallFinder()
        return new(SyntaxNode[])
    end
end

function visit(call_finder::CallFinder, node::SyntaxNode)
    is_call = false
    if kind(node) == K"call" || kind(node) == K"dotcall"
        # check that call does not come from function signature
        # function A(...) ... ~ (function (call A ...) ...)
        if !isnothing(node.parent) && kind(node.parent) == K"function"
            is_call = node.parent[1] != node # is not function signature
        else
            is_call = true
        end
    end
    if is_call
        push!(call_finder.calls, node)
    end
    
    # don't visit nested functions
    if kind(node) == K"function"
        return
    end

    generic_visit(call_finder, node)
end

function get_called_functions(scoped_tree::ScopedTree, node::SyntaxNode)::Vector{SyntaxNode}
    call_finder = CallFinder()
    if kind(node) == K"function"
        body = node[2]
        visit(call_finder, body)
    elseif kind(node) == K"macrocall"
        func = node[2]
        body = func[2]
        visit(call_finder, body)
    else
        visit(call_finder, node)
    end

    # get function definitions for all calls
    called_functions = Vector{SyntaxNode}()
    for call in call_finder.calls
        call_id = get_call_identifier(call)
        for func_def in scoped_tree.all_functions
            func = func_def.node
            func_id = get_function_identifier(func)
            # same name and scope
            if call_id.val == func_id.val && scoped_tree.identifier_to_scope[call_id] == scoped_tree.identifier_to_scope[func_id]
                push!(called_functions, func)
                break
            end
        end
    end

    return called_functions
end


mutable struct CallGraphAnalyzer <: NodeVisitor
    scope_tree::ScopedTree
    call_graph::Dict{SyntaxNode, Vector{SyntaxNode}}
    function CallGraphAnalyzer(scope_tree::ScopedTree)
        return new(scope_tree, Dict{SyntaxNode, Vector{SyntaxNode}}())
    end
end


function visit(visitor::CallGraphAnalyzer, node::SyntaxNode)
    if kind(node) == K"function"
        visitor.call_graph[node] = get_called_functions(visitor.scope_tree, node)
    end
    generic_visit(visitor, node)
end

# call_graph maps function_def -> [function_def]
# node -> [function_def] if node is not nothing
function compute_call_graph(scoped_tree::ScopedTree, node::Union{Nothing,SyntaxNode})
    cga = CallGraphAnalyzer(scoped_tree)
    visit(cga, scoped_tree.root_node)

    if !isnothing(node)
        # get subset called by node
        call_subgraph = Dict{SyntaxNode, Vector{SyntaxNode}}()
        
        called_functions = get_called_functions(scoped_tree, node)
        call_subgraph[node] = copy(called_functions)

        # traverse complete call graph starting from node to get only functions that are reachable from node
        processed = Set()
        to_process = called_functions

        if kind(node) == K"macrocall"
            push!(to_process, node[2]) # also process function of macrocall node
        end

        while !isempty(to_process)
            called = pop!(to_process)
            call_subgraph[called] = cga.call_graph[called]
            push!(processed, called)

            for sub_call in cga.call_graph[called]
                if !(sub_call in processed) && !(sub_call in to_process)
                    push!(to_process, sub_call)
                end
            end
        end

        return call_subgraph
    else
        # return complete call graph
        return cga.call_graph
    end
end